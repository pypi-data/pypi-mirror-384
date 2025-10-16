from typing import Any, Dict, List


def extract_anthropic_tool_calls(
    response_data: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Extract tool calls from Anthropic API response.

    Args:
        response_data: The raw response data from Anthropic API

    Returns:
        List of tool call dictionaries with standardized format
    """
    tool_calls = []

    # Handle None response (e.g., when request is cancelled)
    if response_data is None:
        return tool_calls

    # Check if response has content array
    content = response_data.get("content", [])
    if not isinstance(content, list):
        return tool_calls

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


def extract_anthropic_tool_results(
    response_data: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Extract tool results from Anthropic API response (for tool result blocks).

    Args:
        response_data: The raw response data from Anthropic API

    Returns:
        List of tool result dictionaries
    """
    tool_results = []

    # Handle None response (e.g., when request is cancelled)
    if response_data is None:
        return tool_results

    # Check if response has content array
    content = response_data.get("content", [])
    if not isinstance(content, list):
        return tool_results

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


def extract_anthropic_text_content(response_data: Dict[str, Any]) -> str:
    """
    Extract text content from Anthropic API response, filtering out tool calls.

    Args:
        response_data: The raw response data from Anthropic API

    Returns:
        Concatenated text content
    """
    text_content = ""

    # Handle None response (e.g., when request is cancelled)
    if response_data is None:
        return text_content

    # Check if response has content array
    content = response_data.get("content", [])
    if not isinstance(content, list):
        return text_content

    for content_block in content:
        if (
            isinstance(content_block, dict)
            and content_block.get("type") == "text"
        ):
            text_content += content_block.get("text", "")

    return text_content


def get_anthropic_response_summary(
    response_data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Get a comprehensive summary of Anthropic API response including text and tool calls.

    Args:
        response_data: The raw response data from Anthropic API

    Returns:
        Dictionary containing text content, tool calls, and summary info
    """
    # Handle None response (e.g., when request is cancelled)
    if response_data is None:
        return {
            "text_content": "",
            "tool_calls": [],
            "tool_results": [],
            "has_tool_calls": False,
            "has_tool_results": False,
        }

    tool_calls = extract_anthropic_tool_calls(response_data)
    tool_results = extract_anthropic_tool_results(response_data)
    text_content = extract_anthropic_text_content(response_data)

    return {
        "text_content": text_content,
        "tool_calls": tool_calls,
        "tool_results": tool_results,
        "has_tool_calls": len(tool_calls) > 0,
        "has_tool_results": len(tool_results) > 0,
        "tool_call_count": len(tool_calls),
        "tool_result_count": len(tool_results),
    }


def extract_anthropic_response_with_tools(response_data: Dict[str, Any]):
    """
    Enhanced response extractor for Anthropic that handles both text and tool calls.

    Args:
        response_data: The raw response data from Anthropic API

    Returns:
        Dictionary containing text content and tool call information, or just text for backward compatibility
    """
    response_summary = get_anthropic_response_summary(response_data)

    # Combine text content and tool calls for comprehensive output
    output_content = {
        "text": response_summary["text_content"],
        "tool_calls": response_summary["tool_calls"],
        "tool_results": response_summary["tool_results"],
    }

    # If no tool calls, just return the text for backward compatibility
    if (
        not response_summary["has_tool_calls"]
        and not response_summary["has_tool_results"]
    ):
        return response_summary["text_content"]

    return output_content
