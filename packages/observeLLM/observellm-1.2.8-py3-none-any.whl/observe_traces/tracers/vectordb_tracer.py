"""
OOP vector database tracer implementation.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, List, Optional

from ..base.tracer import BaseTracer
from ..config.context_util import request_context
from ..config.langfuse_service import _LangfuseService
from ..utils.tracer_utils import log_error


class VectorDBTracer(BaseTracer):
    """OOP implementation of vector database tracing."""

    def __init__(
        self,
        provider,
        operation_type: str,
        variable_mapping: Optional[Dict[str, str]] = None,
        metadata_config: Optional[List[str]] = None,
    ):
        super().__init__(provider, variable_mapping, metadata_config)
        self.operation_type = operation_type

    async def trace(self, func: Callable, *args, **kwargs) -> Any:
        """Execute vector database tracing for the function call."""
        if not self.should_trace():
            return await func(*args, **kwargs)

        # STEP 1: Always execute the function first
        try:
            result = await func(*args, **kwargs)
        except Exception as function_error:
            log_error(function_error, "Original function failed")
            raise function_error

        # STEP 2: Function succeeded, now try to add tracing
        try:
            trace_id = request_context.get()
            start_time = datetime.now()
            end_time = datetime.now()
            response_time = end_time - start_time

            # Parse operation data based on operation type
            if self.operation_type == "write":
                operation_data = self.provider.parse_write_response(result)
            else:  # read
                operation_data = self.provider.parse_read_response(result)

            # Calculate cost
            price_data = self.provider.calculate_cost(
                operation_data, operation_data["operation_type"]
            )

            # Create timezone
            ist = timezone(timedelta(hours=5, minutes=30))

            # Get mapped parameter values
            query = self.get_mapped_param_value(kwargs, "query")
            namespace = self.get_mapped_param_value(kwargs, "namespace") or ""
            index_host = self.get_mapped_param_value(kwargs, "index_host") or ""

            # Extract response data
            if self.operation_type == "write":
                vectors_count = result.get("upsertedCount", 0)
                vectors = self.get_mapped_param_value(
                    kwargs, "vectors"
                ) or kwargs.get("vectors", [])
                total_vectors = len(vectors)
                response_data = result
                operation_details = {
                    "index_host": index_host,
                    "namespace": namespace,
                    "upserted_vectors": vectors_count,
                    "total_vectors": total_vectors,
                }
            elif self.operation_type == "read":
                max_results = (
                    self.get_mapped_param_value(kwargs, "max_results")
                    or self.get_mapped_param_value(kwargs, "top_k")
                    or 0
                )
                response_data = result.get("matches", result.get("results", []))
                operation_details = {
                    "index_host": index_host,
                    "namespace": namespace,
                    "top_k": max_results,
                }
            else:
                response_data = result
                operation_details = {}

            span_data = {
                "service_provider": self.provider.name,
                "operation_type": self.operation_type,
                "response": response_data or "",
                "operation_details": operation_details,
                "units": operation_data["units"],
                "price": price_data["price"],
                "query": query,
                "start_time": start_time,
                "end_time": end_time,
                "response_time": response_time,
                "timestamp": datetime.now(ist).strftime("%Y-%m-%d %H:%M:%S"),
            }

            # Build complete metadata
            complete_metadata = {
                **operation_details,
                "operation_type": self.operation_type,
                "provider": self.provider.name,
                "cost": price_data["price"],
                "read_units": operation_data["units"],
            }

            # Filter metadata if metadata_config is provided
            filtered_metadata = self.filter_metadata(complete_metadata)

            await _LangfuseService.create_span_for_vectorDB(
                trace_id=trace_id,
                span_data=span_data,
                name=f"{self.provider.name.capitalize()} {self.operation_type.capitalize()}",
                filtered_metadata=filtered_metadata,
            )

        except Exception as tracing_error:
            log_error(
                tracing_error,
                "Tracing failed - function succeeded, returning result despite tracing failure",
            )

        return result
