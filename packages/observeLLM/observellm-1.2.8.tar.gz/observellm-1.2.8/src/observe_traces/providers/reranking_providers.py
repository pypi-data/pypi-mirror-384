"""
Concrete reranking provider implementations.
"""

from typing import Any, Dict, List

from ..base.provider import RerankingProvider


class PineconeRerankingProvider(RerankingProvider):
    """Pinecone reranking provider implementation."""

    def __init__(self):
        super().__init__(
            name="pinecone", results_extractor=self._extract_pinecone_results
        )

    def parse_tokens(self, response_data: Dict[str, Any]) -> Dict[str, int]:
        """Parse tokens from Pinecone reranking response."""
        usage = response_data.get("usage", {})
        return {"rerank_units": usage.get("rerank_units", 0)}

    def calculate_cost(
        self, tokens_data: Dict[str, int], model_name: str
    ) -> Dict[str, float]:
        """Calculate cost for Pinecone reranking model."""
        pricing = {
            "pinecone-rerank-v0": 0.10,  # $0.10 per 1k rerank units
        }

        rerank_units = tokens_data.get("rerank_units", 0)
        model_price = pricing.get(model_name, 0.0)
        total_price = (rerank_units / 1000) * model_price

        return {
            "rerank_units": rerank_units,
            "price_per_1K": model_price,
            "total": total_price,
        }

    def _extract_pinecone_results(
        self, data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Extract results from Pinecone reranking response."""
        return data.get("data", [])


class CohereRerankingProvider(RerankingProvider):
    """Cohere reranking provider implementation."""

    def __init__(self):
        super().__init__(
            name="cohere", results_extractor=self._extract_cohere_results
        )

    def parse_tokens(self, response_data: Dict[str, Any]) -> Dict[str, int]:
        """Parse tokens from Cohere reranking response."""
        meta = response_data.get("meta", {})
        billed_units = meta.get("billed_units", {})
        return {"search_units": billed_units.get("search_units", 0)}

    def calculate_cost(
        self, tokens_data: Dict[str, int], model_name: str
    ) -> Dict[str, float]:
        """Calculate cost for Cohere reranking model."""
        pricing = {
            "rerank-english-v3.0": 0.15,  # $0.15 per search unit
        }

        search_units = tokens_data.get("search_units", 0)
        model_price = pricing.get(model_name, 0.0)
        total_price = search_units * model_price

        return {
            "search_units": search_units,
            "price_per_unit": model_price,
            "total": total_price,
        }

    def _extract_cohere_results(
        self, data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Extract results from Cohere reranking response."""
        return data.get("results", [])


class JinaRerankingProvider(RerankingProvider):
    """Jina reranking provider implementation."""

    def __init__(self):
        super().__init__(
            name="jina", results_extractor=self._extract_jina_results
        )

    def parse_tokens(self, response_data: Dict[str, Any]) -> Dict[str, int]:
        """Parse tokens from Jina reranking response."""
        usage = response_data.get("usage", {})
        return {"tokens": usage.get("total_tokens", 0)}

    def calculate_cost(
        self, tokens_data: Dict[str, int], model_name: str
    ) -> Dict[str, float]:
        """Calculate cost for Jina reranking model."""
        pricing = {
            "jina-rerank-v1-tiny-en": 0.08,  # $0.08 per 1M tokens
        }

        tokens = tokens_data.get("tokens", 0)
        model_price = pricing.get(model_name, 0.0)
        total_price = (tokens / 1000000) * model_price

        return {
            "tokens": tokens,
            "price_per_1M": model_price,
            "total": total_price,
        }

    def _extract_jina_results(
        self, data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Extract results from Jina reranking response."""
        return data.get("results", [])


class VoyageRerankingProvider(RerankingProvider):
    """Voyage reranking provider implementation."""

    def __init__(self):
        super().__init__(
            name="voyage", results_extractor=self._extract_voyage_results
        )

    def parse_tokens(self, response_data: Dict[str, Any]) -> Dict[str, int]:
        """Parse tokens from Voyage reranking response."""
        usage = response_data.get("usage", {})
        return {"tokens": usage.get("total_tokens", 0)}

    def calculate_cost(
        self, tokens_data: Dict[str, int], model_name: str
    ) -> Dict[str, float]:
        """Calculate cost for Voyage reranking model."""
        pricing = {
            "voyage-rerank-v1": 0.12,  # $0.12 per 1M tokens
        }

        tokens = tokens_data.get("tokens", 0)
        model_price = pricing.get(model_name, 0.0)
        total_price = (tokens / 1000000) * model_price

        return {
            "tokens": tokens,
            "price_per_1M": model_price,
            "total": total_price,
        }

    def _extract_voyage_results(
        self, data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Extract results from Voyage reranking response."""
        return data.get("results", [])
