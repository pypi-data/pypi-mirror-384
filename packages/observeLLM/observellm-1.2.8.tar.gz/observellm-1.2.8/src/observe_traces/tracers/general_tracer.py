"""
General-purpose tracer implementation for any function.
"""

import inspect
from contextvars import ContextVar
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from ..base.tracer import BaseTracer
from ..config.context_util import tracer_context
from ..config.langfuse_service import _LangfuseService

# Context variable to store current span ID for nesting
current_span_context: ContextVar[Optional[str]] = ContextVar(
    "current_span_context", default=None
)


class GeneralTracer(BaseTracer):
    """General-purpose tracer for any function."""

    def __init__(
        self,
        span_name: Optional[str] = None,
        variable_mapping: Optional[Dict[str, str]] = None,
        metadata_config: Optional[List[str]] = None,
    ):
        # Use a dummy provider since this is a general tracer
        class DummyProvider:
            name = "general"

        super().__init__(DummyProvider(), variable_mapping, metadata_config)
        self.span_name = span_name

    async def trace(self, func: Callable, *args, **kwargs) -> Any:
        """Execute general tracing for the function call."""
        if not self.should_trace():
            return await func(*args, **kwargs)

        # Get trace context
        trace = tracer_context.get()
        if not trace:
            return await func(*args, **kwargs)

        start_time = datetime.now()

        # Determine span name
        span_name = self.span_name or func.__name__.replace("_", " ").title()

        # Get current parent span for nesting
        parent_span_id = current_span_context.get()

        # Prepare input data
        input_data = self._prepare_input_data(func, args, kwargs)

        # Clear any previously captured result
        clear_captured_result()

        span_token = None
        actual_span_id = None

        # First, create a placeholder span to get an ID for child spans
        # We'll use a two-phase approach: create span, execute function, then update span
        span_kwargs = {
            "trace_id": trace.id,
            "name": span_name,
            "start_time": start_time,
        }

        if parent_span_id:
            span_kwargs["parent_observation_id"] = parent_span_id

        # Create the initial span to get a span ID
        langfuse_client = _LangfuseService.get_instance().langfuse_client
        span_object = langfuse_client.span(**span_kwargs)
        actual_span_id = span_object.id

        # Set this span ID in context BEFORE executing the function so child spans can reference it
        span_token = current_span_context.set(actual_span_id)

        try:
            # Execute the function (now child spans will have the correct parent ID)
            result = await func(*args, **kwargs)
            end_time = datetime.now()

            # Check if a result was captured (for functions without return values)
            captured_result = get_captured_result()
            output_data = self._prepare_output_data(
                captured_result if captured_result is not None else result
            )

            # Build complete metadata
            complete_metadata = {
                "functionName": func.__name__,
                "timeTaken": (end_time - start_time).total_seconds(),
                "hasReturn": result is not None,
                "hasCapturedResult": captured_result is not None,
                "argumentCount": len(args) + len(kwargs),
                "isAsync": inspect.iscoroutinefunction(func),
                "module": (
                    func.__module__
                    if hasattr(func, "__module__")
                    else "unknown"
                ),
            }

            # Filter metadata if metadata_config is provided
            filtered_metadata = self.filter_metadata(complete_metadata)

            # Update the span with the final input, output, and metadata
            span_object.end(
                end_time=end_time,
                input=input_data,
                output=output_data,
                metadata=(
                    filtered_metadata if filtered_metadata is not None else {}
                ),
            )

            return result

        except Exception as e:
            end_time = datetime.now()

            # Build error metadata
            complete_metadata = {
                "functionName": func.__name__,
                "timeTaken": (end_time - start_time).total_seconds(),
                "hasError": True,
                "errorType": type(e).__name__,
                "argumentCount": len(args) + len(kwargs),
                "isAsync": inspect.iscoroutinefunction(func),
                "module": (
                    func.__module__
                    if hasattr(func, "__module__")
                    else "unknown"
                ),
            }

            # Filter metadata if metadata_config is provided
            filtered_metadata = self.filter_metadata(complete_metadata)

            # Update the span with error information
            span_object.end(
                end_time=end_time,
                input=input_data,
                output={"error": str(e), "error_type": type(e).__name__},
                metadata=(
                    filtered_metadata if filtered_metadata is not None else {}
                ),
            )

            raise e

        finally:
            # Reset the span context
            if span_token:
                current_span_context.reset(span_token)

    def _prepare_input_data(
        self, func: Callable, args: tuple, kwargs: dict
    ) -> Dict[str, Any]:
        """Prepare input data for the span."""
        try:
            # Get function signature
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            # Convert to dictionary, handling special cases
            input_dict = {}
            for param_name, value in bound_args.arguments.items():
                if param_name == "self":
                    input_dict[param_name] = str(type(value).__name__)
                else:
                    input_dict[param_name] = self._serialize_value(value)

            return input_dict
        except Exception:
            # Fallback to simple args/kwargs structure
            return {
                "args": [self._serialize_value(arg) for arg in args],
                "kwargs": {
                    k: self._serialize_value(v) for k, v in kwargs.items()
                },
            }

    def _prepare_output_data(self, result: Any) -> Any:
        """Prepare output data for the span."""
        return self._serialize_value(result)

    def _serialize_value(self, value: Any) -> Any:
        """Serialize a value for JSON storage, handling special types."""
        try:
            # Handle None
            if value is None:
                return None

            # Handle basic types
            if isinstance(value, (str, int, float, bool)):
                return value

            # Handle lists and tuples
            if isinstance(value, (list, tuple)):
                return [
                    self._serialize_value(item) for item in value[:10]
                ]  # Limit to first 10 items

            # Handle dictionaries
            if isinstance(value, dict):
                return {
                    k: self._serialize_value(v)
                    for k, v in list(value.items())[:10]
                }  # Limit to first 10 items

            # Handle objects with string representation
            str_repr = str(value)
            if len(str_repr) > 1000:  # Limit string length
                return str_repr[:1000] + "..."
            return str_repr

        except Exception:
            return f"<{type(value).__name__} object>"


# Context manager for capturing results in functions that don't return anything
class ResultCapture:
    """Context manager for capturing results in functions without return values."""

    def __init__(self):
        self._result = None
        self._captured = False

    def capture_result(self, result: Any) -> None:
        """Capture a result to be used as span output."""
        self._result = result
        self._captured = True

    def get_result(self) -> Any:
        """Get the captured result."""
        return self._result if self._captured else None

    def has_result(self) -> bool:
        """Check if a result was captured."""
        return self._captured


# Global result capture instance that can be imported
_result_capture = ResultCapture()


def capture_result(result: Any) -> None:
    """Global function to capture results for spans."""
    _result_capture.capture_result(result)


def get_captured_result() -> Any:
    """Get the captured result."""
    return _result_capture.get_result()


def clear_captured_result() -> None:
    """Clear the captured result."""
    global _result_capture
    _result_capture = ResultCapture()
