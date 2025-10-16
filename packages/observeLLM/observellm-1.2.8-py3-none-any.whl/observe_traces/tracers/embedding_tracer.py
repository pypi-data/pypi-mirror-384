"""
OOP embedding tracer implementation.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, List, Optional

from ..base.tracer import BaseTracer
from ..config.context_util import request_context
from ..config.langfuse_service import _LangfuseService
from ..utils.tracer_utils import log_error


class EmbeddingTracer(BaseTracer):
    """OOP implementation of embedding tracing."""

    def __init__(
        self,
        provider,
        variable_mapping: Optional[Dict[str, str]] = None,
        metadata_config: Optional[List[str]] = None,
    ):
        super().__init__(provider, variable_mapping, metadata_config)

    async def trace(self, func: Callable, *args, **kwargs) -> Any:
        """Execute embedding tracing for the function call."""
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

            # Parse tokens and calculate cost
            tokens_data = self.provider.parse_tokens(result)

            # Get mapped parameter values
            model_name = self.get_mapped_param_value(kwargs, "model_name")
            inputs = self.get_mapped_param_value(
                kwargs, "inputs"
            ) or self.get_mapped_param_value(kwargs, "texts")

            # Ensure inputs is a list and get count
            if not inputs:
                inputs = []
            elif not isinstance(inputs, list):
                inputs = [inputs]

            input_count = len(inputs)

            # Calculate price
            price_details = {}
            if tokens_data and model_name:
                try:
                    price_details = self.provider.calculate_cost(
                        tokens_data, model_name
                    )
                except Exception:
                    price_details = {"total": 0.0}

            # Extract embeddings
            embeddings = self.provider.extract_embeddings(result)
            embedding_dimensions = (
                len(embeddings[0]) if embeddings and embeddings[0] else 0
            )

            # Create timezone
            ist = timezone(timedelta(hours=5, minutes=30))

            span_data = {
                "service_provider": self.provider.name,
                "model_name": model_name,
                "input": inputs,
                "input_count": input_count,
                "tokens": tokens_data.get("tokens", 0),
                "price": price_details,
                "embedding_dimensions": embedding_dimensions,
                "start_time": start_time,
                "end_time": end_time,
                "response_time": response_time,
                "timestamp": datetime.now(ist).strftime("%Y-%m-%d %H:%M:%S"),
            }

            # Build complete metadata
            complete_metadata = {
                "provider": self.provider.name,
                "model_name": model_name,
                "input count": input_count,
                "cost": price_details.get("total", 0.0),
                "token usage": tokens_data.get("tokens", 0),
                "price": price_details,
                "embedding_dimensions": embedding_dimensions,
                "timestamp": datetime.now(ist).strftime("%Y-%m-%d %H:%M:%S"),
            }

            # Filter metadata if metadata_config is provided
            filtered_metadata = self.filter_metadata(complete_metadata)

            await _LangfuseService.create_span_for_embedding(
                trace_id=trace_id,
                span_data=span_data,
                name=f"{self.provider.name.capitalize()} Embedding",
                filtered_metadata=filtered_metadata,
            )

        except Exception as tracing_error:
            log_error(
                tracing_error,
                "Tracing failed - function succeeded, returning result despite tracing failure",
            )

        return result
