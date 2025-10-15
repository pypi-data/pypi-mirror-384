"""
Paylink Tracer SDK - Simple tracing for payment operations.

This SDK provides simple tracing for payment tools, automatically capturing
execution details and sending them to your Paylink API endpoint.

It now supports multi-tenant MCP setups: the MCP server can inject a dynamic
trace context (headers, project info, etc.) from each tenant request using
`set_trace_context_provider()`.
"""

from paylink_tracer.tracer import (
    paylink_tracer,
    configure,
    set_base_url,
    enable_tracing,
    disable_tracing,
    set_trace_context_provider,
)

__version__ = "0.1.6"

__all__ = [
    "paylink_tracer",
    "configure",
    "set_base_url",
    "enable_tracing",
    "disable_tracing",
    "set_trace_context_provider",  
]
