# Paylink Tracer SDK

Lightweight internal SDK for tracing Paylink payment operations.  

## 🚀 Quick Start

### 1. Install

```bash
uv add paylink-tracer
```

### 2. Configure

Set the required environment variables (or use a `.env` file):

```bash
PAYLINK_API_KEY=plk_live_xxxxx
PAYLINK_PROJECT=Demo Project
PAYMENT_PROVIDER=["mpesa"]
PAYLINK_TRACING=enabled
```

### 3. Use the Decorator

```python
from paylink_tracer import paylink_tracer

@paylink_tracer
async def call_tool(name: str, arguments: dict):
    # Your payment logic here
    return {"status": "success", "message": "Payment processed"}

# Example call
await call_tool("stk_push", {"amount": "1000", "phone": "254700000000"})
```

## 🧠 Notes

- Automatically sends traces to `http://127.0.0.1:8000/api/v1/trace` (local dev)
- Use `set_base_url("https://api.paylink.co.ke")` for production
- Works with async functions
- Automatically captures errors, arguments, and timing
- Disable tracing with `PAYLINK_TRACING=disabled`

## 👨‍💻 Internal Use Only

This SDK is intended for internal Paylink use.  
For issues or updates, contact the Paylink engineering team.

## 📄 License

MIT License - see LICENSE file for details.
