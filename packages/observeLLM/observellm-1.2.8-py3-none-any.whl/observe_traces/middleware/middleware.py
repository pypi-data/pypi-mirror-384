import copy
import json
import time
import uuid
from typing import Any, Dict, List, Optional

from fastapi import Request
from fastapi.responses import StreamingResponse

from ..config.context_util import (
    request_context,
    request_metadata_context,
    tracer_context,
)
from ..config.langfuse_init import LangfuseInitializer


def _preprocess_langfuse_input(input_data: Any) -> Any:
    """
    Preprocess input data to prevent Langfuse's automatic transformation of "messages" keys.

    Args:
        input_data: The original input data

    Returns:
        Processed input data with "messages" keys renamed to avoid automatic parsing
    """
    if input_data is None:
        return input_data

    # Create a deep copy to avoid modifying the original data
    processed_input = copy.deepcopy(input_data)

    def _rename_messages_keys(obj: Any) -> Any:
        """Recursively rename 'messages' keys to 'raw_messages' to prevent auto-parsing"""
        if isinstance(obj, dict):
            new_dict = {}
            for key, value in obj.items():
                if key == "messages":
                    # Rename to prevent Langfuse automatic parsing
                    new_dict["raw_messages"] = _rename_messages_keys(value)
                    # Add a flag to indicate this was transformed
                    new_dict["_langfuse_messages_renamed"] = True
                else:
                    new_dict[key] = _rename_messages_keys(value)
            return new_dict
        elif isinstance(obj, list):
            return [_rename_messages_keys(item) for item in obj]
        else:
            return obj

    return _rename_messages_keys(processed_input)


def _should_trace_route(
    route_path: str,
    include_routes: Optional[List[str]] = None,
    exclude_routes: Optional[List[str]] = None,
) -> bool:
    """
    Determine if a route should be traced based on include/exclude lists.

    Args:
        route_path: The route path to check
        include_routes: List of routes to include for tracing (if provided, only these routes will be traced)
        exclude_routes: List of routes to exclude from tracing

    Returns:
        bool: True if route should be traced, False otherwise

    Priority:
        1. If include_routes is provided, only trace routes in that list
        2. If exclude_routes is provided, trace all routes except those in that list
        3. If both are provided, include_routes takes priority
        4. If neither is provided, trace all routes
    """
    # If include_routes is provided, only trace routes in that list
    if include_routes is not None:
        return route_path in include_routes

    # If exclude_routes is provided, exclude those routes
    if exclude_routes is not None:
        return route_path not in exclude_routes

    # Default: trace all routes
    return True


async def unified_middleware(
    request: Request,
    call_next,
    metadata: Optional[Dict[str, Any]] = None,
    route_mapping: Optional[Dict[str, str]] = None,
    include_routes: Optional[List[str]] = None,
    exclude_routes: Optional[List[str]] = None,
    tag_mapping: Optional[Dict[str, List[str]]] = None,
    input: Optional[Any] = None,
):
    """
    Unified middleware for LLM observability with optional route name mapping, selective tracing, tags support, and input capture.

    Args:
        request: FastAPI request object
        call_next: Next middleware in chain
        metadata: Optional metadata for the trace
        route_mapping: Optional mapping of routes to custom names
                   Example: {"/auth/login": "Authentication with Login", "/user": "User Creation"}
        include_routes: Optional list of routes to include for tracing. If provided, only these routes will be traced.
                       Example: ["/api/chat", "/api/embeddings"]
        exclude_routes: Optional list of routes to exclude from tracing.
                       Example: ["/health", "/metrics", "/docs"]
        tag_mapping: Optional mapping of routes to lists of tags for categorization and filtering
                  Example: {"/api/chat": ["production", "llm"], "/api/embeddings": ["production", "embedding"]}
        input: Optional input data for the trace. Can be any JSON object (e.g., request.body, parsed request data)

    Note:
        - If both include_routes and exclude_routes are provided, include_routes takes priority
        - If a route is not traced, decorators will gracefully skip tracing operations
        - Routes not traced will still process normally but won't create Langfuse traces
        - Tags are used to categorize traces and can be filtered in the Langfuse UI
        - Input data helps track what data was provided to the trace for debugging and analysis
        - Input data containing "messages" keys will be preprocessed to prevent automatic Langfuse transformation
    """
    # Set request context
    session_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request_token = None
    metadata_token = None
    trace_token = None

    # Get the route path from metadata or request
    route_path = metadata.get("apiEndpoint") if metadata else request.url.path

    # Check if this route should be traced
    should_trace = _should_trace_route(
        route_path, include_routes, exclude_routes
    )

    if not should_trace:
        # Skip tracing for this route - just process the request normally
        try:
            response = await call_next(request)

            # Still set basic response headers for consistency
            if response is not None:
                response.headers["X-Request-ID"] = session_id
                response.headers["X-Trace-Status"] = "skipped"

            return response
        except Exception as e:
            print("=" * 40, ">", "Error in non-traced request:", e)
            # return StreamingResponse(
            #     iter(
            #         [json.dumps({"error": f"Internal server error - {str(e)}"})]
            #     ),
            #     status_code=500,
            #     headers={
            #         "X-Request-ID": session_id,
            #         "X-Trace-Status": "skipped",
            #     },
            # )

    # Proceed with tracing for included routes
    trace_id = str(uuid.uuid4())
    langfuse_client = LangfuseInitializer.get_instance().langfuse_client

    if request_context.get() is None:
        request_token = request_context.set(trace_id)

    # Set metadata if provided
    if metadata is not None:
        metadata_token = request_metadata_context.set(metadata)

    # Determine trace name using route_mapping if provided
    if route_mapping and route_path in route_mapping:
        trace_name = route_mapping[route_path]
    else:
        trace_name = route_path if route_path else trace_id

    # Get tags for the current route
    route_tags = tag_mapping.get(route_path, []) if tag_mapping else []

    # Preprocess input to prevent automatic Langfuse transformation
    processed_input = _preprocess_langfuse_input(input)

    if trace_id:
        trace = langfuse_client.trace(
            id=trace_id,
            name=trace_name,
            input=processed_input,  # Use preprocessed input
            session_id=session_id,
            metadata=metadata,
            user_id=metadata.get("user") if metadata else None,
            tags=route_tags,
        )

    trace_token = tracer_context.set(trace)

    request.state.langfuse_context = {
        **(metadata or {}),
        "trace_id": trace_id,
    }

    try:
        # Process the request
        response = await call_next(request)
        end_time = time.time()

        # Ensure we have a valid response before modifying headers
        if response is not None:

            # Set response headers
            response.headers["X-Request-ID"] = session_id
            response.headers["X-Trace-ID"] = trace_id
            response.headers["X-Trace-Status"] = "traced"

            return response
        else:
            print(
                "=" * 40,
                ">",
                "No response returned from call_next from the package",
            )
            # raise RuntimeError("No response returned from call_next")
            return StreamingResponse(
                iter(
                    [
                        json.dumps(
                            {
                                "error": "Internal server error - No response from service"
                            }
                        )
                    ]
                ),
                status_code=500,
                headers={
                    "X-Request-ID": session_id,
                    "X-Trace-ID": trace_id,
                    "X-Trace-Status": "traced",
                },
            )
    except Exception as e:
        print("=" * 40, ">", "Error in the middleware from the package", str(e))
        # return StreamingResponse(
        #     iter([json.dumps({"error": f"Internal server error - {str(e)}"})]),
        #     status_code=500,
        #     headers={
        #         "X-Request-ID": session_id,
        #         "X-Trace-ID": trace_id,
        #         "X-Trace-Status": "traced",
        #     },
        # )
    finally:
        # Clean up context tokens
        if request_token is not None:
            request_context.reset(request_token)
        if metadata_token is not None:
            request_metadata_context.reset(metadata_token)
        if trace_token is not None:
            tracer_context.reset(trace_token)
