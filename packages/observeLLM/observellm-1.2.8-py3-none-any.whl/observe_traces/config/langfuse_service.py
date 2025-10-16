from typing import Any, Dict, Optional

from langfuse import Langfuse

from .context_util import tracer_context


class LangfuseClient:
    def __init__(
        self,
        langfuse_public_key: str,
        langfuse_secret_key: str,
        langfuse_host: str,
        release: str,
        environment: str,
    ):
        self.langfuse_public_key = langfuse_public_key
        self.langfuse_secret_key = langfuse_secret_key
        self.langfuse_host = langfuse_host
        self.release = release
        self.environment = environment
        self.langfuse_client = None

    def initialize_langfuse_client(self):
        self.langfuse_client = Langfuse(
            public_key=self.langfuse_public_key,
            secret_key=self.langfuse_secret_key,
            host=self.langfuse_host,
            release=self.release,
            environment=self.environment,
        )

    def close_langfuse_client(self):
        pass


class _LangfuseService:
    _instance = None

    @classmethod
    def initialize(
        cls,
        langfuse_public_key: str,
        langfuse_secret_key: str,
        langfuse_host: str,
        release: str,
        environment: str,
    ) -> None:
        """Initialize the Langfuse client singleton."""
        if cls._instance is None:
            cls._instance = LangfuseClient(
                langfuse_public_key=langfuse_public_key,
                langfuse_secret_key=langfuse_secret_key,
                langfuse_host=langfuse_host,
                release=release,
                environment=environment,
            )
            cls._instance.initialize_langfuse_client()

    @classmethod
    def get_instance(cls) -> Optional[LangfuseClient]:
        """Get the Langfuse client instance."""
        return cls._instance

    @classmethod
    def close(cls) -> None:
        """Close the Langfuse client instance."""
        if cls._instance is not None:
            cls._instance.close_langfuse_client()
            cls._instance = None

    @staticmethod
    async def create_generation_for_LLM(
        trace_id: str,
        generation_data: Dict[str, Any],
        name: str,
        filtered_metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:

        try:
            trace = tracer_context.get()

            trace.update(
                output=generation_data["output"],
            )

            langfuse_client = _LangfuseService.get_instance().langfuse_client
            generation_object = langfuse_client.generation(
                trace_id=trace_id,
                name=name,
            )

            # Build usage details with cache tokens
            usage_details = {
                "input": generation_data["usage"]["prompt_tokens"],
                "output": generation_data["usage"]["completion_tokens"],
                # "total_token": generation_data["usage"]["total_tokens"],
            }

            # Add cache tokens if present
            if (
                generation_data["usage"].get("cache_creation_input_tokens", 0)
                > 0
            ):
                usage_details["cache_creation_input_tokens"] = generation_data[
                    "usage"
                ]["cache_creation_input_tokens"]

            if generation_data["usage"].get("cache_read_input_tokens", 0) > 0:
                usage_details["cache_read_input_tokens"] = generation_data[
                    "usage"
                ]["cache_read_input_tokens"]

            # Build cost details with cache costs
            base_input_cost = generation_data["cost_details"]["input"]
            base_output_cost = generation_data["cost_details"]["output"]
            cache_creation_cost = generation_data["cost_details"].get(
                "cache_creation", 0.0
            )
            cache_read_cost = generation_data["cost_details"].get(
                "cache_read", 0.0
            )

            # Calculate total cost including cache costs
            total_cost_with_cache = (
                base_input_cost
                + base_output_cost
                + cache_creation_cost
                + cache_read_cost
            )

            cost_details = {
                "input": base_input_cost,
                "output": base_output_cost,
                "total": total_cost_with_cache,  # ✅ FIXED: Include cache costs in total
            }

            # Add cache costs if present
            if cache_creation_cost > 0.0:
                cost_details["cache_creation"] = cache_creation_cost

            if cache_read_cost > 0.0:
                cost_details["cache_read"] = cache_read_cost

            generation_object.end(
                model=generation_data["model_name"],
                input=generation_data["input"],
                output=generation_data["output"],
                usage_details=usage_details,
                cost_details=cost_details,
                metadata=(
                    filtered_metadata
                    if filtered_metadata is not None
                    else {
                        "model": generation_data["model_name"],
                        "provider": generation_data["service_provider"],
                        "maxTokens": generation_data["max_tokens"],
                        "temperature": generation_data["temperature"],
                        "tool": generation_data["tool_names"],
                        "timeTaken": (
                            generation_data["end_time"]
                            - generation_data["start_time"]
                        ).total_seconds(),
                        "inputTokens": generation_data["usage"][
                            "prompt_tokens"
                        ],
                        "outputTokens": generation_data["usage"][
                            "completion_tokens"
                        ],
                        "inputCost": base_input_cost,
                        "outputCost": base_output_cost,
                        "totalCost": total_cost_with_cache,  # ✅ FIXED: Use total cost including cache costs
                        # Cache-specific costs in metadata for detailed tracking
                        **(
                            {"cacheCreationCost": cache_creation_cost}
                            if cache_creation_cost > 0.0
                            else {}
                        ),
                        **(
                            {"cacheReadCost": cache_read_cost}
                            if cache_read_cost > 0.0
                            else {}
                        ),
                        **generation_data.get("tool_call_metadata", {}),
                    }
                ),
            )
            return generation_object.id
        except Exception as e:
            return None

    @staticmethod
    async def create_span_for_vectorDB(
        trace_id: str,
        span_data: Dict[str, Any],
        name: str,
        filtered_metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        try:

            langfuse_client = _LangfuseService.get_instance().langfuse_client
            span_object = langfuse_client.span(
                trace_id=trace_id,
                name=name,
            )

            span_object.end(
                input=span_data["query"],
                output=span_data["response"],
                metadata=(
                    filtered_metadata
                    if filtered_metadata is not None
                    else {
                        **span_data["operation_details"],
                        "operation_type": span_data["operation_type"],
                        "provider": span_data["service_provider"],
                        "cost": span_data["price"],
                        "read_units": span_data["units"],
                    }
                ),
            )

            return span_object.id
        except Exception as e:
            return None

    @staticmethod
    async def create_span_for_embedding(
        trace_id: str,
        span_data: Dict[str, Any],
        name: str,
        filtered_metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:

        try:
            trace = tracer_context.get()

            trace.update(
                input=span_data["input"],
            )

            langfuse_client = _LangfuseService.get_instance().langfuse_client
            span_object = langfuse_client.span(
                trace_id=trace_id,
                name=name,
            )

            span_object.end(
                input=span_data["input"],
                metadata=(
                    filtered_metadata
                    if filtered_metadata is not None
                    else {
                        "provider": span_data["service_provider"],
                        "model_name": span_data["model_name"],
                        "input count": span_data["input_count"],
                        "cost": span_data["price"]["total"],
                        "token usage": span_data["tokens"],
                        "price": span_data["price"],
                        "embedding_dimensions": span_data[
                            "embedding_dimensions"
                        ],
                        "timestamp": span_data["timestamp"],
                    }
                ),
            )

            return span_object.id
        except Exception as e:
            return None

    @staticmethod
    async def create_span_for_reranking(
        trace_id: str,
        span_data: Dict[str, Any],
        name: str,
        filtered_metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        try:
            langfuse_client = _LangfuseService.get_instance().langfuse_client
            span_object = langfuse_client.span(
                trace_id=trace_id,
                name=name,
            )

            span_object.end(
                input={
                    "query": span_data["query"],
                    "documents": span_data["documents"],
                },
                output=span_data["rerank_results"],
                metadata=(
                    filtered_metadata
                    if filtered_metadata is not None
                    else {
                        "provider": span_data["service_provider"],
                        "model_name": span_data["model_name"],
                        "output_count": span_data["document_count"],
                        "cost": span_data["price"],
                        "token usage": span_data["tokens"]["rerank_units"],
                        "timestamp": span_data["timestamp"],
                        "top_n": span_data["top_n"],
                    }
                ),
            )

            return span_object.id
        except Exception as e:
            return None

    @staticmethod
    async def create_span_for_general(
        trace_id: str,
        span_data: Dict[str, Any],
        name: str,
        filtered_metadata: Optional[Dict[str, Any]] = None,
        parent_observation_id: Optional[str] = None,
    ) -> Optional[str]:
        """
        Create a general-purpose span for any function.

        Args:
            trace_id: The trace ID
            span_data: Dict containing input, output, start_time, end_time, function_name
            name: Name of the span
            filtered_metadata: Optional filtered metadata
            parent_observation_id: Optional parent observation ID for nesting

        Returns:
            The span ID if successful, None otherwise
        """
        try:
            langfuse_client = _LangfuseService.get_instance().langfuse_client

            # Create span with optional parent
            span_kwargs = {
                "trace_id": trace_id,
                "name": name,
                "start_time": span_data["start_time"],
            }

            if parent_observation_id:
                span_kwargs["parent_observation_id"] = parent_observation_id

            span_object = langfuse_client.span(**span_kwargs)

            span_object.end(
                end_time=span_data["end_time"],
                input=span_data["input"],
                output=span_data["output"],
                metadata=(
                    filtered_metadata if filtered_metadata is not None else {}
                ),
            )

            return span_object.id
        except Exception as e:
            return None
