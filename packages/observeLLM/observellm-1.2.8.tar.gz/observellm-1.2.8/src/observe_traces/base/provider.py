"""
Base provider classes for different AI services.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Callable, Dict, List


class BaseProvider(ABC):
    """Abstract base class for all AI service providers."""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def parse_tokens(self, response_data: Dict[str, Any]) -> Dict[str, int]:
        """Parse tokens from provider response."""

    @abstractmethod
    def calculate_cost(
        self, tokens_data: Dict[str, int], model_name: str
    ) -> Dict[str, float]:
        """Calculate cost based on tokens and model."""


class LLMProvider(BaseProvider):
    """Base class for LLM providers."""

    def __init__(self, name: str, response_extractor: Callable = None):
        super().__init__(name)
        self.response_extractor = (
            response_extractor or self._default_response_extractor
        )

    @abstractmethod
    def parse_tokens(self, response_data: Dict[str, Any]) -> Dict[str, int]:
        """Parse token usage from LLM response."""

    def extract_response(self, response_data: Dict[str, Any]) -> Any:
        """Extract meaningful response content."""
        # Handle None response (e.g., when request is cancelled)
        if response_data is None:
            return ""
        
        return self.response_extractor(response_data)

    def get_completion_start_time(self, response_data: Dict[str, Any]) -> float:
        """Extract completion start time from response."""
        # Handle None response (e.g., when request is cancelled)
        if response_data is None:
            return datetime.now().timestamp()
        
        return response_data.get("created", datetime.now().timestamp())

    def _default_response_extractor(self, data: Dict[str, Any]) -> str:
        """Default response extractor."""
        return str(data)


class EmbeddingProvider(BaseProvider):
    """Base class for embedding providers."""

    def __init__(self, name: str, embeddings_extractor: Callable = None):
        super().__init__(name)
        self.embeddings_extractor = (
            embeddings_extractor or self._default_embeddings_extractor
        )

    @abstractmethod
    def parse_tokens(self, response_data: Dict[str, Any]) -> Dict[str, int]:
        """Parse token usage from embedding response."""

    def extract_embeddings(
        self, response_data: Dict[str, Any]
    ) -> List[List[float]]:
        """Extract embeddings from response."""
        return self.embeddings_extractor(response_data)

    def _default_embeddings_extractor(
        self, data: Dict[str, Any]
    ) -> List[List[float]]:
        """Default embeddings extractor."""
        return []


class VectorDBProvider(BaseProvider):
    """Base class for vector database providers."""

    def __init__(self, name: str, response_extractor: Callable = None):
        super().__init__(name)
        self.response_extractor = (
            response_extractor or self._default_response_extractor
        )

    @abstractmethod
    def parse_write_response(
        self, response_data: Dict[str, Any]
    ) -> Dict[str, int]:
        """Parse write operation response."""

    @abstractmethod
    def parse_read_response(
        self, response_data: Dict[str, Any]
    ) -> Dict[str, int]:
        """Parse read operation response."""

    def parse_tokens(self, response_data: Dict[str, Any]) -> Dict[str, int]:
        """Not applicable for vector DB, but required by base class."""
        return {}

    def calculate_cost(
        self, operation_data: Dict[str, Any], operation_type: str
    ) -> Dict[str, float]:
        """Calculate cost for vector DB operations."""
        return {"units": 0, "price": 0.0}

    def extract_response(
        self, response_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Extract response data."""
        return self.response_extractor(response_data)

    def _default_response_extractor(
        self, data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Default response extractor."""
        return []


class RerankingProvider(BaseProvider):
    """Base class for reranking providers."""

    def __init__(self, name: str, results_extractor: Callable = None):
        super().__init__(name)
        self.results_extractor = (
            results_extractor or self._default_results_extractor
        )

    @abstractmethod
    def parse_tokens(self, response_data: Dict[str, Any]) -> Dict[str, int]:
        """Parse token usage from reranking response."""

    def extract_results(
        self, response_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Extract reranking results."""
        return self.results_extractor(response_data)

    def _default_results_extractor(
        self, data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Default results extractor."""
        return data.get("results", [])
