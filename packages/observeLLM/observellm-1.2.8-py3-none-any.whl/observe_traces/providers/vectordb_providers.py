"""
Concrete vector database provider implementations.
"""

from typing import Any, Dict, List

from ..base.provider import VectorDBProvider


class PineconeVectorDBProvider(VectorDBProvider):
    """Pinecone vector database provider implementation."""

    def __init__(self):
        super().__init__(
            name="pinecone", response_extractor=self._extract_pinecone_response
        )

    def parse_write_response(
        self, response_data: Dict[str, Any]
    ) -> Dict[str, int]:
        """Parse write operation response from Pinecone."""
        return {
            "operation_type": "write",
            "units": response_data.get("upsertedCount", 0),
        }

    def parse_read_response(
        self, response_data: Dict[str, Any]
    ) -> Dict[str, int]:
        """Parse read operation response from Pinecone."""
        usage = response_data.get("usage", {})
        return {"operation_type": "read", "units": usage.get("read_units", 0)}

    def calculate_cost(
        self, operation_data: Dict[str, Any], operation_type: str
    ) -> Dict[str, float]:
        """Calculate cost for Pinecone operations."""
        pricing = {
            "read": 16.0,  # $16 per million read units
            "write": 4.0,  # $4 per million write units
        }

        units = operation_data.get("units", 0)
        price = (units / 1000000) * pricing.get(operation_type, 0.0)

        return {"units": units, "price": price}

    def _extract_pinecone_response(
        self, data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Extract response data from Pinecone."""
        return [
            {
                "score": match["score"],
                "text": match.get("metadata", {}).get("text", ""),
                "namespace": data.get("namespace", ""),
            }
            for match in data.get("matches", [])
        ]
