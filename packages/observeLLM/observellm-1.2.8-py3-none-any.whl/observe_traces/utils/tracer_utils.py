from typing import Any, Dict, List, Optional, Tuple


def get_mapped_param_value(
    params: Dict[str, Any],
    expected_key: str,
    variable_mapping: Dict[str, str] = None,
):
    """
    Get parameter value using variable mapping if provided, otherwise use expected key.

    Args:
        params: The function parameters dictionary
        expected_key: The expected parameter key (e.g., "system_prompt", "user_prompt")
        variable_mapping: Optional mapping of expected keys to actual parameter names

    Returns:
        The parameter value or None if not found
    """
    if variable_mapping and expected_key in variable_mapping:
        actual_key = variable_mapping[expected_key]
        return params.get(actual_key)
    return params.get(expected_key)


def process_system_prompt(system_prompt: Any) -> Tuple[str, Dict[str, Any]]:
    """
    Process system prompt and extract cache control metadata if present.

    Args:
        system_prompt: The system prompt which can be in various formats:
                      - String format: passed as-is
                      - List format: [{"type": "text", "text": "prompt", "cache_control": {...}}]

    Returns:
        Tuple of (processed_text, cache_metadata)
    """
    cache_metadata = {}

    # Handle list format with cache_control
    if isinstance(system_prompt, list):
        processed_text = ""
        for item in system_prompt:
            if isinstance(item, dict):
                # Extract text content
                if item.get("type") == "text" and "text" in item:
                    processed_text += item["text"]

                # Extract cache_control metadata
                if "cache_control" in item:
                    cache_metadata["systemPromptCacheControl"] = item[
                        "cache_control"
                    ]

        return processed_text, cache_metadata

    # Handle other formats (string, etc.) - pass as-is
    return system_prompt or "", cache_metadata


def convert_anthropic_messages_to_langfuse_format(
    messages: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Convert Anthropic messages to Langfuse format.
    """
    return [
        {"role": msg["role"], "content": msg["content"]} for msg in messages
    ]


def convert_groq_messages_to_langfuse_format(
    messages: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Convert Groq messages to Langfuse format.
    """
    return [
        {"role": msg["role"], "content": msg["content"]} for msg in messages
    ]


def extract_tool_calls_from_messages(
    messages: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Extract tool calls from the messages list.

    Args:
        messages: List of message dictionaries in Anthropic format

    Returns:
        List of tool call dictionaries
    """
    tool_calls = []

    for message in messages:
        if message.get("role") == "assistant":
            content = message.get("content", [])

            # Handle both string content and list content
            if isinstance(content, str):
                continue  # String content doesn't contain tool calls
            elif isinstance(content, list):
                for content_block in content:
                    if (
                        isinstance(content_block, dict)
                        and content_block.get("type") == "tool_use"
                    ):
                        tool_call = {
                            "id": content_block.get("id", ""),
                            "name": content_block.get("name", ""),
                            "input": content_block.get("input", {}),
                            "type": "tool_use",
                        }
                        tool_calls.append(tool_call)

    return tool_calls


def extract_tool_results_from_messages(
    messages: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Extract tool results from the messages list.

    Args:
        messages: List of message dictionaries in Anthropic format

    Returns:
        List of tool result dictionaries
    """
    tool_results = []

    for message in messages:
        if message.get("role") == "user":
            content = message.get("content", [])

            # Handle both string content and list content
            if isinstance(content, str):
                continue  # String content doesn't contain tool results
            elif isinstance(content, list):
                for content_block in content:
                    if (
                        isinstance(content_block, dict)
                        and content_block.get("type") == "tool_result"
                    ):
                        tool_result = {
                            "tool_use_id": content_block.get("tool_use_id", ""),
                            "content": content_block.get("content", ""),
                            "is_error": content_block.get("is_error", False),
                            "type": "tool_result",
                        }
                        tool_results.append(tool_result)

    return tool_results


def get_tool_call_summary_from_messages(
    messages: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Get a summary of tool calls and tool results from the messages list.

    Args:
        messages: List of message dictionaries in Anthropic format

    Returns:
        Dictionary containing tool call and tool result information
    """
    tool_calls = extract_tool_calls_from_messages(messages)
    tool_results = extract_tool_results_from_messages(messages)

    return {
        "tool_calls": tool_calls,
        "tool_results": tool_results,
        "has_tool_calls": len(tool_calls) > 0,
        "has_tool_results": len(tool_results) > 0,
        "tool_call_count": len(tool_calls),
        "tool_result_count": len(tool_results),
    }


def extract_tool_names_from_tools(tools: List[Dict[str, Any]]) -> List[str]:
    """
    Extract tool names from the tools list.
    """
    return [tool.get("name", "Not Found") for tool in tools]


def filter_metadata(
    metadata: Dict[str, Any], metadata_config: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Filter metadata dictionary to only include keys specified in metadata_config.

    Args:
        metadata: The complete metadata dictionary
        metadata_config: Optional list of keys to include. If None, returns all metadata.

    Returns:
        Filtered metadata dictionary
    """
    if metadata_config is None:
        return metadata

    # Return only the keys that are in metadata_config and exist in metadata
    return {
        key: value for key, value in metadata.items() if key in metadata_config
    }


def log_error(error: Exception, context: str = ""):
    """Standardized error logging for the package."""
    error_msg = f"[LLM-Observability Package] {context}: {type(error).__name__}: {error}"
    print(error_msg)
