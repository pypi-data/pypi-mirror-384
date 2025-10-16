from contextvars import ContextVar
from typing import Optional

from fastapi import Request
from langfuse.client import StatefulTraceClient

request_context: ContextVar[Request] = ContextVar(
    "request_context", default=None
)
tracer_context: ContextVar[StatefulTraceClient] = ContextVar(
    "tracer_context", default=None
)
request_metadata_context: ContextVar[dict] = ContextVar(
    "request_metadata_context", default={}
)
generation_id_context: ContextVar[str] = ContextVar(
    "generation_id_context", default=None
)


def get_current_generation_id() -> Optional[str]:
    """
    Get the current generation ID from context.

    Returns:
        str: The current generation ID if available, None otherwise
    """
    return generation_id_context.get()


def set_generation_id(generation_id: str) -> None:
    """
    Set the generation ID in context.

    Args:
        generation_id: The generation ID to store in context
    """
    generation_id_context.set(generation_id)


def clear_generation_id() -> None:
    """
    Clear the generation ID from context.
    """
    generation_id_context.set(None)
