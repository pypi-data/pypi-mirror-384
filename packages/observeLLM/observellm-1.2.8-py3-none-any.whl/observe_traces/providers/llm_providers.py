"""
Concrete LLM provider implementations.
"""

import time
from typing import Any, Dict

from ..base.provider import LLMProvider
from ..utils.token_costs import get_token_costs
from ..utils.tool_call_parser import extract_anthropic_response_with_tools


class OpenAIProvider(LLMProvider):
    """OpenAI LLM provider implementation."""

    def __init__(self):
        super().__init__(
            name="openai", response_extractor=self._extract_openai_response
        )

    def parse_tokens(self, response_data: Dict[str, Any]) -> Dict[str, int]:
        """Parse tokens from OpenAI response."""
        # Handle None response (e.g., when request is cancelled)
        if response_data is None:
            return {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
            }
        
        usage = response_data.get("usage", {})
        return {
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
        }

    def calculate_cost(
        self, tokens_data: Dict[str, int], model_name: str
    ) -> Dict[str, float]:
        """Calculate cost for OpenAI model."""
        try:
            model_pricing = get_token_costs(model_name, self.name)
            prompt_tokens = tokens_data.get("prompt_tokens", 0)
            completion_tokens = tokens_data.get("completion_tokens", 0)

            input_price = prompt_tokens * model_pricing["input_cost_per_token"]
            output_price = (
                completion_tokens * model_pricing["output_cost_per_token"]
            )
            total_price = input_price + output_price

            return {
                "input": input_price,
                "output": output_price,
                "total": total_price,
            }
        except ValueError as e:
            raise e

    def get_completion_start_time(self, response_data: Dict[str, Any]) -> float:
        """Extract completion start time from OpenAI response."""
        return response_data.get("created", time.time())

    def _extract_openai_response(self, data: Dict[str, Any]) -> str:
        """Extract response content from OpenAI response."""
        if "choices" in data and data["choices"]:
            return data["choices"][0]["message"]["content"]
        return ""


class AnthropicProvider(LLMProvider):
    """Anthropic LLM provider implementation."""

    def __init__(self):
        super().__init__(
            name="anthropic",
            response_extractor=extract_anthropic_response_with_tools,
        )

    def parse_tokens(self, response_data: Dict[str, Any]) -> Dict[str, int]:
        """Parse tokens from Anthropic response."""
        # Handle None response (e.g., when request is cancelled)
        if response_data is None:
            return {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "cache_creation_input_tokens": 0,
                "cache_read_input_tokens": 0,
            }
        
        usage = response_data.get("usage", {})
        input_tokens = usage.get("input_tokens", 0)
        output_tokens = usage.get("output_tokens", 0)
        cache_creation_input_tokens = usage.get(
            "cache_creation_input_tokens", 0
        )
        cache_read_input_tokens = usage.get("cache_read_input_tokens", 0)

        return {
            "prompt_tokens": input_tokens,
            "completion_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "cache_creation_input_tokens": cache_creation_input_tokens,
            "cache_read_input_tokens": cache_read_input_tokens,
        }

    def calculate_cost(
        self, tokens_data: Dict[str, int], model_name: str
    ) -> Dict[str, float]:
        """Calculate cost for Anthropic model."""
        try:
            model_pricing = get_token_costs(model_name, self.name)
            prompt_tokens = tokens_data.get("prompt_tokens", 0)
            completion_tokens = tokens_data.get("completion_tokens", 0)
            cache_creation_input_tokens = tokens_data.get(
                "cache_creation_input_tokens", 0
            )
            cache_read_input_tokens = tokens_data.get(
                "cache_read_input_tokens", 0
            )

            input_price = prompt_tokens * model_pricing["input_cost_per_token"]
            output_price = (
                completion_tokens * model_pricing["output_cost_per_token"]
            )

            # Calculate cache-related costs
            cache_creation_price = 0.0
            cache_read_price = 0.0

            if (
                cache_creation_input_tokens > 0
                and "cache_creation_input_token_cost" in model_pricing
            ):
                cache_creation_price = (
                    cache_creation_input_tokens
                    * model_pricing["cache_creation_input_token_cost"]
                )

            if (
                cache_read_input_tokens > 0
                and "cache_read_input_token_cost" in model_pricing
            ):
                cache_read_price = (
                    cache_read_input_tokens
                    * model_pricing["cache_read_input_token_cost"]
                )

            total_price = (
                input_price
                + output_price
                + cache_creation_price
                + cache_read_price
            )

            return {
                "input": input_price,
                "output": output_price,
                "cache_creation": cache_creation_price,
                "cache_read": cache_read_price,
                "total": total_price,
            }
        except ValueError as e:
            raise e

    def get_completion_start_time(self, response_data: Dict[str, Any]) -> float:
        """Extract completion start time from Anthropic response."""
        # Handle None response (e.g., when request is cancelled)
        if response_data is None:
            return time.time()
        
        return response_data.get("started_at", time.time())


class GroqProvider(LLMProvider):
    """Groq LLM provider implementation."""

    def __init__(self):
        super().__init__(
            name="groq", response_extractor=self._extract_groq_response
        )

    def parse_tokens(self, response_data: Dict[str, Any]) -> Dict[str, int]:
        """Parse tokens from Groq response."""
        # Handle None response (e.g., when request is cancelled)
        if response_data is None:
            return {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
            }
        
        usage = response_data.get("usage", {})
        return {
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
        }

    def calculate_cost(
        self, tokens_data: Dict[str, int], model_name: str
    ) -> Dict[str, float]:
        """Calculate cost for Groq model."""
        try:
            model_pricing = get_token_costs(model_name, self.name)
            prompt_tokens = tokens_data.get("prompt_tokens", 0)
            completion_tokens = tokens_data.get("completion_tokens", 0)

            input_price = prompt_tokens * model_pricing["input_cost_per_token"]
            output_price = (
                completion_tokens * model_pricing["output_cost_per_token"]
            )
            total_price = input_price + output_price

            return {
                "input": input_price,
                "output": output_price,
                "total": total_price,
            }
        except ValueError as e:
            raise e

    def get_completion_start_time(self, response_data: Dict[str, Any]) -> float:
        """Extract completion start time from Groq response."""
        return response_data.get("created", time.time())

    def _extract_groq_response(self, data: Dict[str, Any]) -> str:
        """Extract response content from Groq response."""
        if "choices" in data and data["choices"]:
            return data["choices"][0]["message"]["content"]
        return ""


class GeminiProvider(LLMProvider):
    """Gemini LLM provider implementation."""

    def __init__(self):
        super().__init__(
            name="gemini", response_extractor=self._extract_gemini_response
        )

    def parse_tokens(self, response_data: Dict[str, Any]) -> Dict[str, int]:
        """Parse tokens from Gemini response with detailed modality breakdown."""
        # Handle None response (e.g., when request is cancelled)
        if response_data is None:
            return {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
            }
        
        usage = response_data.get("usageMetadata", {})

        # Basic token counts
        tokens_data = {
            "prompt_tokens": usage.get("promptTokenCount", 0),
            "completion_tokens": usage.get("candidatesTokenCount", 0),
            "total_tokens": usage.get("totalTokenCount", 0),
        }

        # Extract detailed token breakdown by modality
        prompt_details = usage.get("promptTokensDetails", [])
        candidates_details = usage.get("candidatesTokensDetails", [])

        # Parse prompt tokens by modality
        for detail in prompt_details:
            if isinstance(detail, dict):
                modality = detail.get("modality", "").lower()
                token_count = detail.get("tokenCount", 0)
                if modality:
                    tokens_data[f"prompt_{modality}_tokens"] = token_count

        # Parse completion tokens by modality
        for detail in candidates_details:
            if isinstance(detail, dict):
                modality = detail.get("modality", "").lower()
                token_count = detail.get("tokenCount", 0)
                if modality:
                    tokens_data[f"completion_{modality}_tokens"] = token_count

        return tokens_data

    def calculate_cost(
        self, tokens_data: Dict[str, int], model_name: str
    ) -> Dict[str, float]:
        """Calculate cost for Gemini model."""
        try:
            model_pricing = get_token_costs(model_name, self.name)
            prompt_tokens = tokens_data.get("prompt_tokens", 0)
            completion_tokens = tokens_data.get("completion_tokens", 0)

            input_price = prompt_tokens * model_pricing["input_cost_per_token"]
            output_price = (
                completion_tokens * model_pricing["output_cost_per_token"]
            )
            total_price = input_price + output_price

            return {
                "input": input_price,
                "output": output_price,
                "total": total_price,
            }
        except ValueError as e:
            raise e

    def get_completion_start_time(self, response_data: Dict[str, Any]) -> float:
        """Extract completion start time from Gemini response."""
        create_time = response_data.get("createTime")
        if create_time:
            # Convert ISO timestamp to Unix timestamp
            from datetime import datetime

            try:
                dt = datetime.fromisoformat(create_time.replace("Z", "+00:00"))
                return dt.timestamp()
            except ValueError:
                pass
        return time.time()

    def _extract_gemini_response(self, data: Dict[str, Any]) -> str:
        """Extract response content from Gemini response."""
        candidates = data.get("candidates", [])
        if not candidates:
            return ""

        candidate = candidates[0]
        content = candidate.get("content", {})
        parts = content.get("parts", [])

        response_text = ""
        for part in parts:
            if "text" in part:
                response_text += part["text"]

        return response_text
