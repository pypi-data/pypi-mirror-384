from typing import Any, Dict, Optional

from fastapi import Request

from ..config.langfuse_init import LangfuseInitializer


def trace_api_call(
    request: Request,
    name: str,
    input_data: Optional[Dict[str, Any]] = None,
    output_data: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Creates a span within an existing trace to log API calls.

    Args:
        request: The FastAPI request object containing trace context
        name: Name of the API call/span
        input_data: Input data of the API call
        output_data: Output data of the API call
        metadata: Additional metadata for the span

    Returns:
        The span ID as a string
    """
    try:
        if not hasattr(request.state, "langfuse_context"):
            # If no langfuse_context (route excluded from tracing), return a dummy span ID
            return "skipped-span-id"

        langfuse_context = request.state.langfuse_context
        trace_id = langfuse_context.get("trace_id")

        if not trace_id:
            # If no trace_id (route excluded from tracing), return a dummy span ID
            return "skipped-span-id"

        langfuse_client = LangfuseInitializer.get_instance().langfuse_client
        trace = langfuse_client.trace(id=trace_id)

        # Create a span within the trace
        span = trace.span(
            name=name,
            input=input_data,
            output=output_data,
            metadata=metadata or {},
        )

        return span.id
    except Exception as e:
        return "skipped-span-id"
