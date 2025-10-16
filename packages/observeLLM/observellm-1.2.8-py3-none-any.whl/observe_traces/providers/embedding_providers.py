"""
Concrete embedding provider implementations.
"""

from typing import Any, Dict, List

from ..base.provider import EmbeddingProvider


class PineconeEmbeddingProvider(EmbeddingProvider):
    """Pinecone embedding provider implementation."""

    def __init__(self):
        super().__init__(
            name="pinecone",
            embeddings_extractor=self._extract_pinecone_embeddings,
        )

    def parse_tokens(self, response_data: Dict[str, Any]) -> Dict[str, int]:
        """Parse tokens from Pinecone embedding response."""
        if "usage" in response_data:
            usage = response_data.get("usage", {})
            return {"tokens": usage.get("total_tokens", 0)}
        return {"tokens": 0}

    def calculate_cost(
        self, tokens_data: Dict[str, int], model_name: str
    ) -> Dict[str, float]:
        """Calculate cost for Pinecone embedding model."""
        pricing = {
            "llama-text-embed-v2": 0.16,
            "multilingual-e5-large": 0.08,
            "pinecone-sparse-english-v0": 0.08,
        }

        tokens = tokens_data.get("tokens", 0)
        model_price = pricing.get(model_name, 0.0)
        total_price = (tokens / 1000000) * model_price

        return {
            "tokens": tokens,
            "price_per_1M": model_price,
            "total": total_price,
        }

    def _extract_pinecone_embeddings(
        self, data: Dict[str, Any]
    ) -> List[List[float]]:
        """Extract embeddings from Pinecone response."""
        return [item["values"] for item in data.get("data", [])]


class CohereEmbeddingProvider(EmbeddingProvider):
    """Cohere embedding provider implementation."""

    def __init__(self):
        super().__init__(
            name="cohere", embeddings_extractor=self._extract_cohere_embeddings
        )

    def parse_tokens(self, response_data: Dict[str, Any]) -> Dict[str, int]:
        """Parse tokens from Cohere embedding response."""
        meta = response_data.get("meta", {})
        billed_units = meta.get("billed_units", {})
        return {"tokens": billed_units.get("input_tokens", 0)}

    def calculate_cost(
        self, tokens_data: Dict[str, int], model_name: str
    ) -> Dict[str, float]:
        """Calculate cost for Cohere embedding model."""
        pricing = {
            "embed-english-v3.0": 0.1,
            "embed-multilingual-v3.0": 0.1,
        }

        tokens = tokens_data.get("tokens", 0)
        model_price = pricing.get(model_name, 0.0)
        total_price = (tokens / 1000000) * model_price

        return {
            "tokens": tokens,
            "price_per_1M": model_price,
            "total": total_price,
        }

    def _extract_cohere_embeddings(
        self, data: Dict[str, Any]
    ) -> List[List[float]]:
        """Extract embeddings from Cohere response."""
        return data.get("embeddings", {}).get("float", [])


class JinaEmbeddingProvider(EmbeddingProvider):
    """Jina embedding provider implementation."""

    def __init__(self):
        super().__init__(
            name="jina", embeddings_extractor=self._extract_jina_embeddings
        )

    def parse_tokens(self, response_data: Dict[str, Any]) -> Dict[str, int]:
        """Parse tokens from Jina embedding response."""
        usage = response_data.get("usage", {})
        return {"tokens": usage.get("total_tokens", 0)}

    def calculate_cost(
        self, tokens_data: Dict[str, int], model_name: str
    ) -> Dict[str, float]:
        """Calculate cost for Jina embedding model."""
        pricing = {
            "jina-embeddings-v2-base-en": 0.05,
            "jina-embeddings-v3": 0.12,
            "jina-embeddings-v2-base-code": 0.05,
        }

        tokens = tokens_data.get("tokens", 0)
        model_price = pricing.get(model_name, 0.0)
        total_price = (tokens / 1000000) * model_price

        return {
            "tokens": tokens,
            "price_per_1M": model_price,
            "total": total_price,
        }

    def _extract_jina_embeddings(
        self, data: Dict[str, Any]
    ) -> List[List[float]]:
        """Extract embeddings from Jina response."""
        return [item["embedding"] for item in data.get("data", [])]


class VoyageAIEmbeddingProvider(EmbeddingProvider):
    """VoyageAI embedding provider implementation."""

    def __init__(self):
        super().__init__(
            name="voyageai",
            embeddings_extractor=self._extract_voyageai_embeddings,
        )

    def parse_tokens(self, response_data: Dict[str, Any]) -> Dict[str, int]:
        """Parse tokens from VoyageAI embedding response."""
        usage = response_data.get("usage", {})
        return {"tokens": usage.get("total_tokens", 0)}

    def calculate_cost(
        self, tokens_data: Dict[str, int], model_name: str
    ) -> Dict[str, float]:
        """Calculate cost for VoyageAI embedding model."""
        pricing = {
            "voyage-3": 0.06,
            "voyage-3-lite": 0.02,
            "voyage-finance-2": 0.12,
            "voyage-law-2": 0.12,
            "voyage-code-2": 0.12,
            "voyage-code-3": 0.18,
            "voyage-3-large": 0.18,
        }

        tokens = tokens_data.get("tokens", 0)
        model_price = pricing.get(model_name, 0.0)
        total_price = (tokens / 1000000) * model_price

        return {
            "tokens": tokens,
            "price_per_1M": model_price,
            "total": total_price,
        }

    def _extract_voyageai_embeddings(
        self, data: Dict[str, Any]
    ) -> List[List[float]]:
        """Extract embeddings from VoyageAI response."""
        return [item["embedding"] for item in data.get("data", [])]
