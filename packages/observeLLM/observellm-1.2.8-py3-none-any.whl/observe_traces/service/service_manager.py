"""
Main service manager for the observability framework.
"""

import functools
from typing import Any, Callable, Dict, List, Optional

from ..base.tracer import tracer_manager
from ..providers import (
    AnthropicProvider,
    CohereEmbeddingProvider,
    CohereRerankingProvider,
    GeminiProvider,
    GroqProvider,
    JinaEmbeddingProvider,
    JinaRerankingProvider,
    OpenAIProvider,
    PineconeEmbeddingProvider,
    PineconeRerankingProvider,
    PineconeVectorDBProvider,
    VoyageAIEmbeddingProvider,
    VoyageRerankingProvider,
)
from ..tracers import (
    EmbeddingTracer,
    GeneralTracer,
    LLMStreamingTracer,
    LLMTracer,
    RerankingTracer,
    VectorDBTracer,
)


class ObservabilityService:
    """Main service manager for AI observability with OOP design."""

    def __init__(self):
        self._setup_providers()

    def _setup_providers(self):
        """Setup all default providers."""
        # Register LLM providers
        tracer_manager.register_llm_provider("openai", OpenAIProvider())
        tracer_manager.register_llm_provider("anthropic", AnthropicProvider())
        tracer_manager.register_llm_provider("groq", GroqProvider())
        tracer_manager.register_llm_provider("gemini", GeminiProvider())

        # Register embedding providers
        tracer_manager.register_embedding_provider(
            "pinecone", PineconeEmbeddingProvider()
        )
        tracer_manager.register_embedding_provider(
            "cohere", CohereEmbeddingProvider()
        )
        tracer_manager.register_embedding_provider(
            "jina", JinaEmbeddingProvider()
        )
        tracer_manager.register_embedding_provider(
            "voyageai", VoyageAIEmbeddingProvider()
        )

        # Register vector DB providers
        tracer_manager.register_vectordb_provider(
            "pinecone", PineconeVectorDBProvider()
        )

        # Register reranking providers
        tracer_manager.register_reranking_provider(
            "pinecone", PineconeRerankingProvider()
        )
        tracer_manager.register_reranking_provider(
            "cohere", CohereRerankingProvider()
        )
        tracer_manager.register_reranking_provider(
            "jina", JinaRerankingProvider()
        )
        tracer_manager.register_reranking_provider(
            "voyage", VoyageRerankingProvider()
        )

    def register_llm_provider(self, name: str, provider):
        """Register a custom LLM provider."""
        tracer_manager.register_llm_provider(name, provider)

    def register_embedding_provider(self, name: str, provider):
        """Register a custom embedding provider."""
        tracer_manager.register_embedding_provider(name, provider)

    def register_vectordb_provider(self, name: str, provider):
        """Register a custom vector DB provider."""
        tracer_manager.register_vectordb_provider(name, provider)

    def register_reranking_provider(self, name: str, provider):
        """Register a custom reranking provider."""
        tracer_manager.register_reranking_provider(name, provider)

    def llm_tracing(
        self,
        provider: str,
        variable_mapping: Optional[Dict[str, str]] = None,
        metadata_config: Optional[List[str]] = None,
        is_sdk: bool = False,
    ):
        """
        Decorator for tracing LLM API calls with provider-specific handling.

        Args:
            provider: Name of the LLM provider (e.g., "openai", "anthropic", "groq")
            variable_mapping: Optional mapping of expected parameter names to actual parameter names
            metadata_config: Optional list of metadata keys to include. If None, includes all metadata.
            is_sdk: Whether to treat the function as SDK mode (returns complete response) or standard mode (default: False)
        """

        def decorator(func):
            @functools.wraps(func)
            async def wrapper(self, **params):
                provider_instance = tracer_manager.get_llm_provider(provider)
                if not provider_instance:
                    return await func(self, **params)
                tracer = LLMTracer(
                    provider_instance, variable_mapping, metadata_config, is_sdk
                )
                return await tracer.trace(func, self, **params)

            return wrapper

        return decorator

    def llm_streaming_tracing(
        self,
        provider: str,
        variable_mapping: Optional[Dict[str, str]] = None,
        metadata_config: Optional[List[str]] = None,
        is_sdk: bool = False,
    ):
        """
        Decorator for tracing streaming LLM API calls.
        Currently only supports Anthropic provider.

        Args:
            provider: Name of the LLM provider (must be "anthropic")
            variable_mapping: Optional mapping of expected parameter names to actual parameter names
            metadata_config: Optional list of metadata keys to include. If None, includes all metadata.
            is_sdk: Whether to treat the function as SDK mode (returns complete response) or streaming mode (async generator)
        """

        def decorator(func):
            if is_sdk:
                # NEW SDK mode: Return async generator function that handles anthropic_final_message events
                @functools.wraps(func)
                async def wrapper(self, **params):
                    provider_instance = tracer_manager.get_llm_provider(
                        provider
                    )
                    if not provider_instance:
                        async for response_line in func(self, **params):
                            yield response_line
                        return

                    tracer = LLMStreamingTracer(
                        provider_instance,
                        variable_mapping,
                        metadata_config,
                        is_sdk,
                    )
                    async for response_line in tracer.trace(
                        func, self, **params
                    ):
                        yield response_line

                return wrapper
            else:
                # Streaming mode: Return async generator function
                @functools.wraps(func)
                async def wrapper(self, **params):
                    provider_instance = tracer_manager.get_llm_provider(
                        provider
                    )
                    if not provider_instance:
                        async for response_line in func(self, **params):
                            yield response_line
                        return

                    tracer = LLMStreamingTracer(
                        provider_instance,
                        variable_mapping,
                        metadata_config,
                        is_sdk,
                    )
                    async for response_line in tracer.trace(
                        func, self, **params
                    ):
                        yield response_line

                return wrapper

        return decorator

    def embedding_tracing(
        self,
        provider: str,
        variable_mapping: Optional[Dict[str, str]] = None,
        metadata_config: Optional[List[str]] = None,
    ):
        """
        Decorator for tracing embedding API calls with provider-specific handling.

        Args:
            provider: Name of the embedding provider (e.g., "pinecone", "cohere", "jina", "voyageai")
            variable_mapping: Optional mapping of expected parameter names to actual parameter names
            metadata_config: Optional list of metadata keys to include. If None, includes all metadata.
        """

        def decorator(func):
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                provider_instance = tracer_manager.get_embedding_provider(
                    provider
                )
                if not provider_instance:
                    return await func(*args, **kwargs)

                tracer = EmbeddingTracer(
                    provider_instance, variable_mapping, metadata_config
                )
                return await tracer.trace(func, *args, **kwargs)

            return wrapper

        return decorator

    def vectordb_tracing(
        self,
        provider: str,
        operation_type: str,
        variable_mapping: Optional[Dict[str, str]] = None,
        metadata_config: Optional[List[str]] = None,
    ):
        """
        Decorator for tracing Vector DB API calls.

        Args:
            provider: Name of the vector DB provider (e.g., "pinecone")
            operation_type: Type of operation ("read" or "write")
            variable_mapping: Optional mapping of expected parameter names to actual parameter names
            metadata_config: Optional list of metadata keys to include. If None, includes all metadata.
        """

        def decorator(func):
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                provider_instance = tracer_manager.get_vectordb_provider(
                    provider
                )
                if not provider_instance:
                    return await func(*args, **kwargs)

                tracer = VectorDBTracer(
                    provider_instance,
                    operation_type,
                    variable_mapping,
                    metadata_config,
                )
                return await tracer.trace(func, *args, **kwargs)

            return wrapper

        return decorator

    def reranking_tracing(
        self,
        provider: str,
        variable_mapping: Optional[Dict[str, str]] = None,
        metadata_config: Optional[List[str]] = None,
    ):
        """
        Decorator for tracing reranking API calls with provider-specific handling.

        Args:
            provider: Name of the reranking provider (e.g., "pinecone", "cohere", "jina", "voyage")
            variable_mapping: Optional mapping of expected parameter names to actual parameter names
            metadata_config: Optional list of metadata keys to include. If None, includes all metadata.
        """

        def decorator(func):
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                provider_instance = tracer_manager.get_reranking_provider(
                    provider
                )
                if not provider_instance:
                    return await func(*args, **kwargs)

                tracer = RerankingTracer(
                    provider_instance, variable_mapping, metadata_config
                )
                return await tracer.trace(func, *args, **kwargs)

            return wrapper

        return decorator

    def general_tracing(
        self,
        name: Optional[str] = None,
        variable_mapping: Optional[Dict[str, str]] = None,
        metadata_config: Optional[List[str]] = None,
    ):
        """
        General-purpose decorator for tracing any function.

        Args:
            name: Optional name for the span. If not provided, uses function name.
            variable_mapping: Optional mapping of expected parameter names to actual parameter names
            metadata_config: Optional list of metadata keys to include. If None, includes all metadata.

        Examples:
            # Case 1: Normal function with return value
            @general_tracing()
            async def my_function(param1, param2):
                result = some_operation(param1, param2)
                return result

            # Case 2: Function without return value using capture_result
            from observe_traces import capture_result

            @general_tracing()
            async def my_void_function(param1, param2):
                result = some_operation(param1, param2)
                capture_result(result)  # Capture result for tracing
                # No return statement

            # Case 3: Custom span name
            @general_tracing(name="Custom Operation Name")
            async def my_function():
                pass

            # Case 4: Metadata filtering
            @general_tracing(metadata_config=["functionName", "timeTaken"])
            async def my_function():
                pass
        """

        def decorator(func):
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                tracer = GeneralTracer(
                    span_name=name,
                    variable_mapping=variable_mapping,
                    metadata_config=metadata_config,
                )
                return await tracer.trace(func, *args, **kwargs)

            return wrapper

        return decorator


# Global service instance
observability_service = ObservabilityService()


# Convenience functions that maintain backward compatibility
def llm_tracing(
    provider: str,
    variable_mapping: Optional[Dict[str, str]] = None,
    metadata_config: Optional[List[str]] = None,
    is_sdk: bool = False,
):
    """Backward compatible LLM tracing decorator."""
    return observability_service.llm_tracing(
        provider, variable_mapping, metadata_config, is_sdk
    )


def llm_streaming_tracing(
    provider: str,
    variable_mapping: Optional[Dict[str, str]] = None,
    metadata_config: Optional[List[str]] = None,
    is_sdk: bool = False,
):
    """Backward compatible LLM streaming tracing decorator."""
    return observability_service.llm_streaming_tracing(
        provider, variable_mapping, metadata_config, is_sdk
    )


def embedding_tracing(
    provider: str,
    variable_mapping: Optional[Dict[str, str]] = None,
    metadata_config: Optional[List[str]] = None,
):
    """Backward compatible embedding tracing decorator."""
    return observability_service.embedding_tracing(
        provider, variable_mapping, metadata_config
    )


def vectordb_tracing(
    provider: str,
    operation_type: str,
    variable_mapping: Optional[Dict[str, str]] = None,
    metadata_config: Optional[List[str]] = None,
):
    """Backward compatible vector DB tracing decorator."""
    return observability_service.vectordb_tracing(
        provider, operation_type, variable_mapping, metadata_config
    )


def reranking_tracing(
    provider: str,
    variable_mapping: Optional[Dict[str, str]] = None,
    metadata_config: Optional[List[str]] = None,
):
    """Backward compatible reranking tracing decorator."""
    return observability_service.reranking_tracing(
        provider, variable_mapping, metadata_config
    )


def general_tracing(
    name: Optional[str] = None,
    variable_mapping: Optional[Dict[str, str]] = None,
    metadata_config: Optional[List[str]] = None,
):
    """
    General-purpose decorator for tracing any function.

    Args:
        name: Optional name for the span. If not provided, uses function name.
        variable_mapping: Optional mapping of expected parameter names to actual parameter names
        metadata_config: Optional list of metadata keys to include. If None, includes all metadata.

    Examples:
        # Case 1: Normal function with return value
        @general_tracing()
        async def my_function(param1, param2):
            result = some_operation(param1, param2)
            return result

        # Case 2: Function without return value using capture_result
        from observe_traces import capture_result

        @general_tracing()
        async def my_void_function(param1, param2):
            result = some_operation(param1, param2)
            capture_result(result)  # Capture result for tracing
            # No return statement

        # Case 3: Custom span name
        @general_tracing(name="Custom Operation Name")
        async def my_function():
            pass

        # Case 4: Metadata filtering
        @general_tracing(metadata_config=["functionName", "timeTaken"])
        async def my_function():
            pass
    """
    return observability_service.general_tracing(
        name, variable_mapping, metadata_config
    )


def register_provider(
    provider_name: str, token_parser: Callable, response_extractor: Callable
):
    """Backward compatible provider registration for LLM providers."""
    from ..base.provider import LLMProvider

    class CustomLLMProvider(LLMProvider):
        def __init__(self):
            super().__init__(provider_name, response_extractor)

        def parse_tokens(self, response_data: Dict[str, Any]) -> Dict[str, int]:
            return token_parser(response_data)

        def calculate_cost(
            self, tokens_data: Dict[str, int], model_name: str
        ) -> Dict[str, float]:
            # Default implementation - can be enhanced
            return {"input": 0.0, "output": 0.0, "total": 0.0}

    observability_service.register_llm_provider(
        provider_name, CustomLLMProvider()
    )


def register_embedding_provider(
    provider_name: str,
    token_parser: Callable,
    price_calculator: Callable,
    embeddings_extractor: Callable,
):
    """Backward compatible provider registration for embedding providers."""
    from ..base.provider import EmbeddingProvider

    class CustomEmbeddingProvider(EmbeddingProvider):
        def __init__(self):
            super().__init__(provider_name, embeddings_extractor)

        def parse_tokens(self, response_data: Dict[str, Any]) -> Dict[str, int]:
            return token_parser(response_data)

        def calculate_cost(
            self, tokens_data: Dict[str, int], model_name: str
        ) -> Dict[str, float]:
            return price_calculator(model_name, tokens_data)

    observability_service.register_embedding_provider(
        provider_name, CustomEmbeddingProvider()
    )


def register_reranking_provider(
    provider_name: str,
    token_parser: Callable,
    price_calculator: Callable,
    rerank_results_extractor: Callable,
):
    """Backward compatible provider registration for reranking providers."""
    from ..base.provider import RerankingProvider

    class CustomRerankingProvider(RerankingProvider):
        def __init__(self):
            super().__init__(provider_name, rerank_results_extractor)

        def parse_tokens(self, response_data: Dict[str, Any]) -> Dict[str, int]:
            return token_parser(response_data)

        def calculate_cost(
            self, tokens_data: Dict[str, int], model_name: str
        ) -> Dict[str, float]:
            return price_calculator(model_name, tokens_data)

    observability_service.register_reranking_provider(
        provider_name, CustomRerankingProvider()
    )
