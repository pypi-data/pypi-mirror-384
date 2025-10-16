from langfuse.client import StatefulTraceClient

from .context_util import request_context, tracer_context


def get_request_id() -> str:
    return request_context.get()


def get_tracer() -> StatefulTraceClient:
    return tracer_context.get()
