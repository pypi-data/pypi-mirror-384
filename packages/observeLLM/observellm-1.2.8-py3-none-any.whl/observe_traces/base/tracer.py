"""
Base tracer classes and tracer management.
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional

from ..config.context_util import request_context
from ..utils.tracer_utils import filter_metadata, get_mapped_param_value


class BaseTracer(ABC):
    """Abstract base class for all tracers."""

    def __init__(
        self,
        provider,
        variable_mapping: Optional[Dict[str, str]] = None,
        metadata_config: Optional[List[str]] = None,
    ):
        self.provider = provider
        self.variable_mapping = variable_mapping or {}
        self.metadata_config = metadata_config

    @abstractmethod
    async def trace(self, func: Callable, *args, **kwargs) -> Any:
        """Execute tracing for the function call."""

    def get_mapped_param_value(
        self, params: Dict[str, Any], expected_key: str
    ) -> Any:
        """Get parameter value using variable mapping."""
        return get_mapped_param_value(
            params, expected_key, self.variable_mapping
        )

    def filter_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Filter metadata based on metadata_config."""
        return filter_metadata(metadata, self.metadata_config)

    def should_trace(self) -> bool:
        """Check if tracing should be performed."""
        trace_id = request_context.get()
        return trace_id is not None


class TracerManager:
    """Manages all tracers and providers."""

    def __init__(self):
        self._llm_providers = {}
        self._embedding_providers = {}
        self._vectordb_providers = {}
        self._reranking_providers = {}

    def register_llm_provider(self, name: str, provider):
        """Register an LLM provider."""
        self._llm_providers[name] = provider

    def register_embedding_provider(self, name: str, provider):
        """Register an embedding provider."""
        self._embedding_providers[name] = provider

    def register_vectordb_provider(self, name: str, provider):
        """Register a vector DB provider."""
        self._vectordb_providers[name] = provider

    def register_reranking_provider(self, name: str, provider):
        """Register a reranking provider."""
        self._reranking_providers[name] = provider

    def get_llm_provider(self, name: str):
        """Get LLM provider by name."""
        return self._llm_providers.get(name)

    def get_embedding_provider(self, name: str):
        """Get embedding provider by name."""
        return self._embedding_providers.get(name)

    def get_vectordb_provider(self, name: str):
        """Get vector DB provider by name."""
        return self._vectordb_providers.get(name)

    def get_reranking_provider(self, name: str):
        """Get reranking provider by name."""
        return self._reranking_providers.get(name)


# Global tracer manager instance
tracer_manager = TracerManager()
