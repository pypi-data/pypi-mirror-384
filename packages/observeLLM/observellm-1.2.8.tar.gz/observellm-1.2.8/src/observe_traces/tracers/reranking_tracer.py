"""
OOP reranking tracer implementation.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, List, Optional

from ..base.tracer import BaseTracer
from ..config.context_util import request_context
from ..config.langfuse_service import _LangfuseService
from ..utils.tracer_utils import log_error


class RerankingTracer(BaseTracer):
    """OOP implementation of reranking tracing."""

    def __init__(
        self,
        provider,
        variable_mapping: Optional[Dict[str, str]] = None,
        metadata_config: Optional[List[str]] = None,
    ):
        super().__init__(provider, variable_mapping, metadata_config)

    async def trace(self, func: Callable, *args, **kwargs) -> Any:
        """Execute reranking tracing for the function call."""
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
            query = self.get_mapped_param_value(kwargs, "query")
            documents = self.get_mapped_param_value(kwargs, "documents")
            top_n = self.get_mapped_param_value(kwargs, "top_n")

            # Ensure documents is a list
            if not documents:
                documents = []
            elif not isinstance(documents, list):
                documents = [documents]

            document_count = len(documents)

            # Calculate price
            price_details = 0.0
            if tokens_data and model_name:
                try:
                    cost_data = self.provider.calculate_cost(
                        tokens_data, model_name
                    )
                    price_details = cost_data.get("total", 0.0)
                except Exception:
                    price_details = 0.0

            # Extract reranking results
            rerank_results = self.provider.extract_results(result)

            # Create timezone
            ist = timezone(timedelta(hours=5, minutes=30))

            span_data = {
                "service_provider": self.provider.name,
                "model_name": model_name,
                "query": query,
                "documents": documents,
                "document_count": document_count,
                "rerank_results": rerank_results,
                "tokens": tokens_data,
                "price": price_details,
                "top_n": top_n,
                "start_time": start_time,
                "end_time": end_time,
                "response_time": response_time,
                "timestamp": datetime.now(ist).strftime("%Y-%m-%d %H:%M:%S"),
            }

            # Build complete metadata
            complete_metadata = {
                "provider": self.provider.name,
                "model_name": model_name,
                "output_count": document_count,
                "cost": price_details,
                "token usage": tokens_data.get("rerank_units", 0),
                "timestamp": datetime.now(ist).strftime("%Y-%m-%d %H:%M:%S"),
                "top_n": top_n,
            }

            # Filter metadata if metadata_config is provided
            filtered_metadata = self.filter_metadata(complete_metadata)

            await _LangfuseService.create_span_for_reranking(
                trace_id=trace_id,
                span_data=span_data,
                name=f"{self.provider.name.capitalize()} Reranking",
                filtered_metadata=filtered_metadata,
            )

        except Exception as tracing_error:
            log_error(
                tracing_error,
                "Tracing failed - function succeeded, returning result despite tracing failure",
            )

        return result
