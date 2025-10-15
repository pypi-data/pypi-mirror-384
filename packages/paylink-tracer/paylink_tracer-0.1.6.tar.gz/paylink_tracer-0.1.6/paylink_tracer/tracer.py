"""Simple payment tracer for Paylink (multi-tenant, header-first)."""

import uuid
import time
import json
import urllib.request
import urllib.error
from typing import Any, Dict, Optional, Callable
from functools import wraps
import os
import platform
from datetime import datetime

# ---------------------------------------------------------------------------
# Global configuration (optional fallbacks; headers take precedence)
# ---------------------------------------------------------------------------
_config = {
    "base_url": "http://127.0.0.1:8000",  # local dev default
    "api_key": None,                      # fallback if no header auth is provided
    "project_name": None,                 # fallback if no header
    "payment_provider": None,             # fallback if no header
    "enabled": True,
}

_trace_context_provider: Optional[Callable[[], Optional[Dict[str, Any]]]] = None


# ---------------------------------------------------------------------------
# Small utilities
# ---------------------------------------------------------------------------
def _parse_bool(val: Any, default: bool) -> bool:
    if isinstance(val, bool):
        return val
    if isinstance(val, str):
        return val.strip().lower() in {"1", "true", "yes", "on", "enabled"}
    return default


def _normalize_header_dict(headers: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not isinstance(headers, dict):
        return {}
    norm: Dict[str, Any] = {}
    for k, v in headers.items():
        if isinstance(k, str):
            norm[k.strip().lower().replace("_", "-")] = v
    return norm


def _extract_payment_provider(provider_value: Any) -> Optional[str]:
    """Accepts 'mpesa', '["mpesa"]', or ['mpesa'] and returns 'mpesa'."""
    if not provider_value:
        return None
    if isinstance(provider_value, str) and provider_value.startswith("[") and provider_value.endswith("]"):
        try:
            parsed = json.loads(provider_value)
            return parsed[0] if isinstance(parsed, list) and parsed else None
        except (json.JSONDecodeError, IndexError):
            return provider_value
    if isinstance(provider_value, list):
        return provider_value[0] if provider_value else None
    return provider_value


def _generate_meta(parent_trace_id: Optional[str] = None) -> Dict[str, Any]:
    return {
        "span_id": uuid.uuid4().hex[:10],
        "parent_trace_id": parent_trace_id,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


def _get_environment_info() -> Dict[str, Any]:
    return {
        "mcp_protocol_version": "2025-06-18",
        "sdk_version": "1.0.0",
        "runtime": f"python-{platform.python_version()}",
        "os": f"{platform.system()}-{platform.release()}",
        "host": platform.node(),
    }


def _get_config_value(key: str, default: Any = None) -> Any:
    if key == "base_url":
        return _config["base_url"]
    if _config.get(key) is not None:
        return _config[key]
    env_map = {
        "api_key": "PAYLINK_API_KEY",
        "project_name": "PAYLINK_PROJECT",
        "payment_provider": "PAYMENT_PROVIDER",
        "enabled": "PAYLINK_TRACING",
    }
    env_var = env_map.get(key)
    if env_var is None:
        return default
    value = os.getenv(env_var, default)
    if key == "enabled":
        return _parse_bool(value, True if default is None else bool(default))
    if key == "payment_provider" and value:
        return _extract_payment_provider(value)
    return value


# ---------------------------------------------------------------------------
# Request-context helpers (multi-tenant)
# ---------------------------------------------------------------------------
def set_trace_context_provider(fn: Callable[[], Optional[Dict[str, Any]]]) -> None:
    """Register a callable returning the current per-request trace_context dict."""
    global _trace_context_provider
    _trace_context_provider = fn


def _get_request_context_from_provider() -> Optional[Dict[str, Any]]:
    """Return a compact request context with normalized headers."""
    if not _trace_context_provider:
        return None
    try:
        provided = _trace_context_provider()
        if isinstance(provided, dict):
            req = provided.get("request", provided) or {}
            headers = _normalize_header_dict(req.get("headers"))
            return {
                "method": req.get("method"),
                "path": req.get("path"),
                "client": req.get("client"),
                "server": req.get("server"),
                "headers": headers,
            }
    except Exception:
        return None
    return None


def _resolve_headers(kwargs: Dict[str, Any]) -> Dict[str, Any]:
    """Prefer explicit kwargs['trace_context'], otherwise use provider."""
    ctx = kwargs.get("trace_context")
    if isinstance(ctx, dict):
        req = ctx.get("request", {}) or {}
        return _normalize_header_dict(req.get("headers"))
    rc = _get_request_context_from_provider()
    return rc.get("headers", {}) if isinstance(rc, dict) else {}


def _resolve_project_name(headers: Dict[str, Any]) -> str:
    return headers.get("paylink-project") or _get_config_value("project_name", "unknown") or "unknown"


def _resolve_payment_provider(headers: Dict[str, Any], kwargs: Dict[str, Any]) -> str:
    header_val = headers.get("payment-provider")
    if header_val:
        return _extract_payment_provider(header_val) or "unknown"
    tc = kwargs.get("trace_context")
    if isinstance(tc, dict):
        env_data = tc.get("environment") or {}
        if env_data.get("payment_provider"):
            return _extract_payment_provider(env_data["payment_provider"]) or "unknown"
    return _get_config_value("payment_provider", "unknown") or "unknown"


def _resolve_api_key(headers: Dict[str, Any]) -> Optional[str]:
    return (
        headers.get("paylink-api-key")
        or headers.get("x-paylink-api-key")
        or headers.get("authorization")
        or _get_config_value("api_key")
    )


# ---------------------------------------------------------------------------
# Result parsing & status
# ---------------------------------------------------------------------------
def _determine_trace_status(result: Any) -> str:
    try:
        if isinstance(result, list) and result:
            first = result[0]
            if hasattr(first, "text"):
                text_content = first.text
            else:
                if isinstance(first, dict):
                    st = str(first.get("status", "")).lower()
                    return "success" if st == "success" else ("error" if st in {"error", "failed", "failure"} else "unknown")
                return "unknown"
        elif isinstance(result, str):
            text_content = result
        elif isinstance(result, dict):
            st = str(result.get("status", "")).lower()
            return "success" if st == "success" else ("error" if st in {"error", "failed", "failure"} else "unknown")
        else:
            return "unknown"

        try:
            parsed = json.loads(text_content)
            if isinstance(parsed, dict):
                st = str(parsed.get("status", "")).lower()
                if st in {"success", "error", "failed", "failure"}:
                    return "success" if st == "success" else "error"
        except (json.JSONDecodeError, TypeError):
            pass

        tl = text_content.lower() if isinstance(text_content, str) else ""
        if any(w in tl for w in ["error", "failed", "failure", "exception"]):
            return "error"
        if any(w in tl for w in ["success", "accepted", "completed"]):
            return "success"
    except Exception:
        pass
    return "unknown"


def _extract_result_text(result: Any) -> Any:
    if isinstance(result, list):
        out = []
        for item in result:
            if hasattr(item, "text"):
                t = item.text
                if isinstance(t, str):
                    try:
                        out.append(json.loads(t))
                        continue
                    except (json.JSONDecodeError, TypeError):
                        pass
                out.append(t)
            else:
                out.append(item)
        return out[0] if len(out) == 1 else out
    if isinstance(result, str):
        try:
            return json.loads(result)
        except (json.JSONDecodeError, TypeError):
            return result
    return result


def _coerce_response_to_dict(status: str, response: Any) -> Dict[str, Any]:
    """Ensure tracing API always receives a dict for 'response'."""
    if isinstance(response, dict):
        return response
    # If it's a list with a single dict, unwrap
    if isinstance(response, list) and len(response) == 1 and isinstance(response[0], dict):
        return response[0]
    # Fallback: wrap raw value
    return {
        "status_hint": status,
        "raw": response,
    }


# ---------------------------------------------------------------------------
# Transport
# ---------------------------------------------------------------------------
def _send_trace_to_api(
    base_url: str,
    trace_data: Dict[str, Any],
    api_key: Optional[str] = None,
) -> None:
    """Send trace data to the API endpoint."""
    endpoint = f"{base_url.rstrip('/')}/api/v1/trace/"

    data = json.dumps(trace_data, default=str).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    request = urllib.request.Request(endpoint, data=data, headers=headers, method="POST")

    class HTTPRedirectHandler(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            """Handle redirect while preserving POST data for 307/308."""
            if code in (307, 308):
                return urllib.request.Request(
                    newurl,
                    data=req.data,
                    headers=req.headers,
                    origin_req_host=req.origin_req_host,
                    unverifiable=req.unverifiable,
                )
            return super().redirect_request(req, fp, code, msg, headers, newurl)

    try:
        opener = urllib.request.build_opener(HTTPRedirectHandler)
        with opener.open(request, timeout=10.0) as resp:
            if getattr(resp, "status", 200) >= 400:
                response_body = resp.read().decode("utf-8", errors="replace")
                print(f"[Paylink Tracer] Failed to send trace: HTTP {resp.status}")
                print(f"[Paylink Tracer] Response: {response_body}")
                print(f"[Paylink Tracer] Endpoint: {endpoint}")
                print(f"[Paylink Tracer] API Key present: {bool(api_key)}")
    except urllib.error.HTTPError as e:
        try:
            response_body = e.read().decode("utf-8", errors="replace")
        except Exception:
            response_body = "Unable to read response body"
        print(f"[Paylink Tracer] HTTP Error {e.code}: {e.reason}")
        print(f"[Paylink Tracer] Response: {response_body}")
        print(f"[Paylink Tracer] Endpoint: {endpoint}")
        print(f"[Paylink Tracer] API Key present: {bool(api_key)}")
        if e.code == 403:
            print("[Paylink Tracer] Authentication failed. Provide paylink-api-key/Authorization in client headers or set api_key via configure().")
    except urllib.error.URLError as e:
        print(f"[Paylink Tracer] Network error: {e.reason}")
        print(f"[Paylink Tracer] Endpoint: {endpoint}")
    except Exception as e:
        if _get_config_value("enabled", True):
            print(f"[Paylink Tracer] Error sending trace: {type(e).__name__}: {e}")


# ---------------------------------------------------------------------------
# Optional public config (only for single-tenant / CLI usage)
# ---------------------------------------------------------------------------
def configure(
    api_key: str,
    project_name: str,
    payment_provider: str = "mpesa",
    enabled: bool = True,
) -> None:
    """Optional: set global fallbacks. Not required in header-driven multi-tenant setups."""
    _config["api_key"] = api_key
    _config["project_name"] = project_name
    _config["payment_provider"] = payment_provider
    _config["enabled"] = enabled


def set_base_url(url: str) -> None:
    _config["base_url"] = url


def enable_tracing() -> None:
    _config["enabled"] = True


def disable_tracing() -> None:
    _config["enabled"] = False


# ---------------------------------------------------------------------------
# Decorator
# ---------------------------------------------------------------------------
def paylink_tracer(func):
    """Trace payment tool calls with tenant context from headers (multi-tenant)."""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        print("\n" + "=" * 80)
        print("[Paylink Tracer] RECEIVED CALL")
        print("=" * 80)

        if not _get_config_value("enabled", True):
            print("[Paylink Tracer] Tracing is DISABLED - skipping")
            return await func(*args, **kwargs)

        base_url = _get_config_value("base_url")
        if not base_url:
            print("[Paylink Tracer] No base_url configured - skipping")
            return await func(*args, **kwargs)

        start_time = time.time()

        tool_name = kwargs.get("name") or (args[0] if args else "unknown")
        arguments = kwargs.get("arguments") or (args[1] if len(args) > 1 else {})

        trace_id = str(uuid.uuid4())
        request_id = kwargs.get("request_id") or f"req_{uuid.uuid4().hex[:10]}"
        parent_trace_id = kwargs.get("parent_trace_id")

        # Resolve tenant context from headers (provider/kwargs)
        headers = _resolve_headers(kwargs)
        project_name = _resolve_project_name(headers)
        payment_provider = _resolve_payment_provider(headers, kwargs)
        api_key = _resolve_api_key(headers)

        meta = _generate_meta(parent_trace_id)
        environment = _get_environment_info()
        request_context = _get_request_context_from_provider()  # includes normalized headers

        print("\n[Paylink Tracer] EXTRACTED:")
        print(f"  Tool: {tool_name}")
        print(f"  Tenant Project: {project_name}")
        print(f"  Payment Provider: {payment_provider}")
        print(f"  API Key present: {bool(api_key)}")

        status = "success"
        result = None
        error = None

        try:
            result = await func(*args, **kwargs)
        except Exception as e:
            status = "error"
            error = str(e)
            raise
        finally:
            duration_ms = round((time.time() - start_time) * 1000, 2)

            if status == "success" and result is not None:
                status = _determine_trace_status(result)

            raw_response = _extract_result_text(result) if result is not None else {}
            response_dict = _coerce_response_to_dict(status, raw_response)
            if error:
                # add error info to response dict for observability
                response_dict.setdefault("error", error)

            trace_payload = {
                "trace_id": trace_id,
                "request_id": request_id,
                "tool_name": tool_name,
                "project_name": project_name,
                "payment_provider": payment_provider,
                "arguments": arguments,
                "response": response_dict,   # ✅ always a dict
                "status": status,
                "duration_ms": duration_ms,
                "request_context": request_context,
                "environment": environment,
                "meta": meta,
            }

            _send_trace_to_api(
                base_url=base_url,
                trace_data=trace_payload,
                api_key=api_key,
            )
            print("=" * 80 + "\n")

        return result

    return wrapper
