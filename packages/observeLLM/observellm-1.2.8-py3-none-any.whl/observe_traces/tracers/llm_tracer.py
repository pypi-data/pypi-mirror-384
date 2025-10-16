"""
OOP LLM tracer implementation.
"""

import json
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from ..base.tracer import BaseTracer
from ..config.context_util import generation_id_context, request_context
from ..config.langfuse_service import _LangfuseService
from ..utils.tool_call_parser import get_anthropic_response_summary
from ..utils.tracer_utils import (
    convert_anthropic_messages_to_langfuse_format,
    convert_groq_messages_to_langfuse_format,
    extract_tool_names_from_tools,
    get_tool_call_summary_from_messages,
    process_system_prompt,
)


class LLMTracer(BaseTracer):
    """OOP implementation of LLM tracing."""

    def __init__(
        self,
        provider,
        variable_mapping: Optional[Dict[str, str]] = None,
        metadata_config: Optional[List[str]] = None,
        is_sdk: bool = False,
    ):
        super().__init__(provider, variable_mapping, metadata_config)
        self.is_sdk = is_sdk

    async def trace(self, func: Callable, *args, **kwargs) -> Any:
        """Execute LLM tracing for the function call."""
        if not self.should_trace():
            return await func(*args, **kwargs)

        trace_id = request_context.get()
        start_time = datetime.now()

        # Execute the function - if this fails, it's a function error that should be raised
        try:
            result = await func(*args, **kwargs)
            end_time = datetime.now()
        except Exception:
            # This is an error from the decorated function itself - raise it
            raise

        # Handle SDK mode for different providers - tracing errors here should be logged
        try:
            if self.is_sdk and self.provider.name == "anthropic":
                return await self._handle_anthropic_sdk_mode(
                    result, trace_id, start_time, end_time, **kwargs
                )
            elif self.is_sdk and self.provider.name == "openai":
                return await self._handle_openai_sdk_mode(
                    result, trace_id, start_time, end_time, **kwargs
                )
        except Exception as e:
            # This is a tracing error in SDK mode handling - log it but return result
            print(f"[LANGFUSE] Error in SDK mode handling: {e}")
            return result

        # Process result and create trace - tracing errors here should be logged
        try:
            # Handle different result formats (existing logic)
            if isinstance(result, tuple):
                response_data = result[0] if len(result) > 0 else None
                raw_response = result[1] if len(result) > 1 else None
                llm_response = (
                    self.provider.extract_response(raw_response)
                    if raw_response
                    else response_data
                )
                tokens_data = (
                    self.provider.parse_tokens(raw_response)
                    if raw_response
                    else {}
                )
                completion_start_time = (
                    self.provider.get_completion_start_time(raw_response)
                    if raw_response
                    else None
                )
            else:
                raw_response = result
                llm_response = self.provider.extract_response(raw_response)
                tokens_data = self.provider.parse_tokens(raw_response)
                completion_start_time = self.provider.get_completion_start_time(
                    raw_response
                )

            # Get mapped parameter values
            model_name = self.get_mapped_param_value(
                kwargs, "model_name"
            ) or self.get_mapped_param_value(kwargs, "model")
            raw_system_prompt = self.get_mapped_param_value(
                kwargs, "system_prompt"
            )
            system_prompt, system_prompt_cache_metadata = process_system_prompt(
                raw_system_prompt
            )
            user_prompt = self.get_mapped_param_value(
                kwargs, "chat_messages"
            ) or self.get_mapped_param_value(kwargs, "user_prompt")
            operation_name = self.get_mapped_param_value(
                kwargs, "operation_name"
            )
            max_tokens = self.get_mapped_param_value(kwargs, "max_tokens")
            temperature = self.get_mapped_param_value(kwargs, "temperature")
            tools = self.get_mapped_param_value(kwargs, "tools")
            if tools:
                tool_names = extract_tool_names_from_tools(tools)
            else:
                tool_names = []

            # Calculate cost
            cost_details = {}
            if tokens_data and model_name:
                try:
                    cost_details = self.provider.calculate_cost(
                        tokens_data, model_name
                    )
                except ValueError as e:
                    # Cost calculation error - this should still be raised as it's part of expected functionality
                    raise e

            # Extract tool call information for Anthropic provider
            tool_call_metadata = {}
            if self.provider.name == "anthropic" and raw_response:
                response_summary = get_anthropic_response_summary(raw_response)
                tool_call_metadata = {
                    "hasToolCalls": response_summary["has_tool_calls"],
                    "toolCallCount": response_summary["tool_call_count"],
                    "hasToolResults": response_summary["has_tool_results"],
                    "toolResultCount": response_summary["tool_result_count"],
                }
            input_messages = []
            input_messages.append({"role": "system", "content": system_prompt})
            # Convert Anthropic messages to Langfuse format
            if self.provider.name == "anthropic":
                input_messages += convert_anthropic_messages_to_langfuse_format(
                    user_prompt
                )
            elif self.provider.name == "groq":
                input_messages += convert_groq_messages_to_langfuse_format(
                    user_prompt
                )
            else:
                input_messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ]

            generation_data = {
                "model_name": model_name,
                "service_provider": self.provider.name,
                "input": input_messages,
                "output": llm_response,
                "usage": tokens_data,
                "cost_details": cost_details,
                "start_time": start_time,
                "end_time": end_time,
                "tool_call_metadata": tool_call_metadata,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "tool_names": tool_names,
            }

            # Build complete metadata
            complete_metadata = {
                "model": model_name,
                "provider": self.provider.name,
                "maxTokens": max_tokens,
                "temperature": temperature,
                "tool": tool_names,
                "timeTaken": (end_time - start_time).total_seconds(),
                "inputTokens": tokens_data.get("prompt_tokens", 0),
                "outputTokens": tokens_data.get("completion_tokens", 0),
                "inputCost": cost_details.get("input", 0.0),
                "outputCost": cost_details.get("output", 0.0),
                "totalCost": cost_details.get("total", 0.0),
                "originalResponse": raw_response,
                **tool_call_metadata,
                **system_prompt_cache_metadata,
            }

            # Add Gemini-specific modality token breakdown if available
            if self.provider.name == "gemini":
                # Add prompt modality tokens
                if "prompt_text_tokens" in tokens_data:
                    complete_metadata["promptTextTokens"] = tokens_data[
                        "prompt_text_tokens"
                    ]
                if "prompt_image_tokens" in tokens_data:
                    complete_metadata["promptImageTokens"] = tokens_data[
                        "prompt_image_tokens"
                    ]
                if "prompt_audio_tokens" in tokens_data:
                    complete_metadata["promptAudioTokens"] = tokens_data[
                        "prompt_audio_tokens"
                    ]
                if "prompt_video_tokens" in tokens_data:
                    complete_metadata["promptVideoTokens"] = tokens_data[
                        "prompt_video_tokens"
                    ]

                # Add completion modality tokens
                if "completion_text_tokens" in tokens_data:
                    complete_metadata["completionTextTokens"] = tokens_data[
                        "completion_text_tokens"
                    ]
                if "completion_image_tokens" in tokens_data:
                    complete_metadata["completionImageTokens"] = tokens_data[
                        "completion_image_tokens"
                    ]
                if "completion_audio_tokens" in tokens_data:
                    complete_metadata["completionAudioTokens"] = tokens_data[
                        "completion_audio_tokens"
                    ]

            # Filter metadata if metadata_config is provided
            filtered_metadata = self.filter_metadata(complete_metadata)
            generation_id = await _LangfuseService.create_generation_for_LLM(
                trace_id,
                generation_data,
                (
                    operation_name.replace("_", " ").title()
                    if operation_name
                    else f"{self.provider.name.capitalize()} Generation"
                ),
                filtered_metadata,
            )

            generation_id_context.set(generation_id)

        except Exception as e:
            # This is a tracing/decorator error - log it but don't break the function result
            import traceback

            print(f"[LANGFUSE] Error in LLM tracing: {e}")
            print(traceback.format_exc())

        # Always return the original result, even if tracing fails
        return result

    async def _handle_anthropic_sdk_mode(
        self, result, trace_id, start_time, end_time, **kwargs
    ):
        """
        Handle SDK mode for Anthropic.
        Extract usage data directly from the SDK response object.
        """
        try:
            if result is None:
                print(
                    "[LANGFUSE] Warning: SDK result is None, skipping tracing"
                )
                return result

            # In SDK mode, we work directly with the SDK response object
            # Don't use provider methods that expect dictionaries
            sdk_response = result

            # Extract response text directly from SDK object
            llm_response = ""
            for content_block in sdk_response.content:
                if content_block.type == "text":
                    llm_response += content_block.text

            # Extract tokens directly from SDK object
            tokens_data = {
                "prompt_tokens": sdk_response.usage.input_tokens,
                "completion_tokens": sdk_response.usage.output_tokens,
                "total_tokens": sdk_response.usage.input_tokens
                + sdk_response.usage.output_tokens,
                "cache_creation_input_tokens": sdk_response.usage.cache_creation_input_tokens,
                "cache_read_input_tokens": sdk_response.usage.cache_read_input_tokens,
            }

            # Extract tool calls directly from SDK object
            tool_calls = []
            for content_block in sdk_response.content:
                if content_block.type == "tool_use":
                    tool_calls.append(
                        {
                            "id": content_block.id,
                            "name": content_block.name,
                            "input": content_block.input,
                            "type": "tool_use",
                        }
                    )

            # Get mapped parameter values
            model_name = self.get_mapped_param_value(
                kwargs, "model_name"
            ) or self.get_mapped_param_value(kwargs, "model")
            raw_system_prompt = self.get_mapped_param_value(
                kwargs, "system_prompt"
            )
            system_prompt, system_prompt_cache_metadata = process_system_prompt(
                raw_system_prompt
            )
            user_prompt = self.get_mapped_param_value(
                kwargs, "chat_messages"
            ) or self.get_mapped_param_value(kwargs, "user_prompt")
            operation_name = self.get_mapped_param_value(
                kwargs, "operation_name"
            )
            max_tokens = self.get_mapped_param_value(kwargs, "max_tokens")
            temperature = self.get_mapped_param_value(kwargs, "temperature")
            tools = self.get_mapped_param_value(kwargs, "tools")

            if tools:
                tool_names = extract_tool_names_from_tools(tools)
            else:
                tool_names = []

            # Calculate cost using provider method (this should work with tokens_data dict)
            cost_details = {}
            if tokens_data and model_name:
                try:
                    cost_details = self.provider.calculate_cost(
                        tokens_data, model_name
                    )
                except ValueError as e:
                    raise e

            # Create tool call metadata from extracted tool calls
            tool_call_metadata = {
                "hasToolCalls": len(tool_calls) > 0,
                "toolCallCount": len(tool_calls),
                "hasToolResults": False,  # SDK response doesn't contain tool results
                "toolResultCount": 0,
            }

            input_messages = []
            input_messages.append({"role": "system", "content": system_prompt})
            # Convert Anthropic messages to Langfuse format
            if self.provider.name == "anthropic":
                input_messages += convert_anthropic_messages_to_langfuse_format(
                    user_prompt
                )
            elif self.provider.name == "groq":
                input_messages += convert_groq_messages_to_langfuse_format(
                    user_prompt
                )
            else:
                input_messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ]

            generation_data = {
                "model_name": model_name,
                "service_provider": self.provider.name,
                "input": input_messages,
                "output": llm_response,
                "usage": tokens_data,
                "cost_details": cost_details,
                "start_time": start_time,
                "end_time": end_time,
                "tool_call_metadata": tool_call_metadata,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "tool_names": tool_names,
            }

            # Build complete metadata with cache information for Anthropic
            complete_metadata = {
                "model": model_name,
                "provider": self.provider.name,
                "maxTokens": max_tokens,
                "temperature": temperature,
                "tool": tool_names,
                "timeTaken": (end_time - start_time).total_seconds(),
                "inputTokens": tokens_data.get("prompt_tokens", 0),
                "outputTokens": tokens_data.get("completion_tokens", 0),
                "cacheCreationInputTokens": tokens_data.get(
                    "cache_creation_input_tokens", 0
                ),
                "cacheReadInputTokens": tokens_data.get(
                    "cache_read_input_tokens", 0
                ),
                "inputCost": cost_details.get("input", 0.0),
                "outputCost": cost_details.get("output", 0.0),
                "cacheCreationCost": cost_details.get("cache_creation", 0.0),
                "cacheReadCost": cost_details.get("cache_read", 0.0),
                "totalCost": cost_details.get("total", 0.0),
                "sdkMode": True,
                "originalResponse": sdk_response,
                **tool_call_metadata,
                **system_prompt_cache_metadata,
            }

            # Add Gemini-specific modality token breakdown if available
            if self.provider.name == "gemini":
                if "prompt_text_tokens" in tokens_data:
                    complete_metadata["promptTextTokens"] = tokens_data[
                        "prompt_text_tokens"
                    ]
                if "prompt_image_tokens" in tokens_data:
                    complete_metadata["promptImageTokens"] = tokens_data[
                        "prompt_image_tokens"
                    ]
                if "completion_text_tokens" in tokens_data:
                    complete_metadata["completionTextTokens"] = tokens_data[
                        "completion_text_tokens"
                    ]
                if "completion_image_tokens" in tokens_data:
                    complete_metadata["completionImageTokens"] = tokens_data[
                        "completion_image_tokens"
                    ]

            # Filter metadata if metadata_config is provided
            filtered_metadata = self.filter_metadata(complete_metadata)

            generation_id = await _LangfuseService.create_generation_for_LLM(
                trace_id,
                generation_data,
                (
                    operation_name.replace("_", " ").title()
                    if operation_name
                    else f"{self.provider.name.capitalize()} Generation"
                ),
                filtered_metadata,
            )

            generation_id_context.set(generation_id)
            return result

        except Exception as e:
            # This is a tracing/decorator error - log it but don't break the function result
            import traceback

            print(f"[LANGFUSE] Error in SDK mode tracing: {e}")
            print(traceback.format_exc())
            # Return the original result even if tracing fails
            return result

    async def _handle_openai_sdk_mode(
        self, result, trace_id, start_time, end_time, **kwargs
    ):
        """
        Handle SDK mode for OpenAI.
        Extract usage data directly from the OpenAI SDK response object.
        """
        try:
            if result is None:
                print(
                    "[LANGFUSE] Warning: OpenAI SDK result is None, skipping tracing"
                )
                return result

            # In SDK mode, we work directly with the OpenAI SDK response object
            # Don't use provider methods that expect dictionaries
            sdk_response = result

            # Extract response text directly from OpenAI SDK object
            # OpenAI response structure: choices[0].message.content
            llm_response = ""
            if sdk_response.choices and len(sdk_response.choices) > 0:
                message = sdk_response.choices[0].message
                if message.content:
                    llm_response = message.content

            # Extract tokens directly from OpenAI SDK object
            # OpenAI structure: usage.prompt_tokens, usage.completion_tokens, usage.total_tokens
            tokens_data = {
                "prompt_tokens": (
                    sdk_response.usage.prompt_tokens
                    if sdk_response.usage
                    else 0
                ),
                "completion_tokens": (
                    sdk_response.usage.completion_tokens
                    if sdk_response.usage
                    else 0
                ),
                "total_tokens": (
                    sdk_response.usage.total_tokens if sdk_response.usage else 0
                ),
            }

            # Extract tool calls directly from OpenAI SDK object
            # OpenAI structure: choices[0].message.tool_calls
            tool_calls = []
            if sdk_response.choices and len(sdk_response.choices) > 0:
                message = sdk_response.choices[0].message
                if hasattr(message, "tool_calls") and message.tool_calls:
                    for tool_call in message.tool_calls:
                        tool_calls.append(
                            {
                                "id": tool_call.id,
                                "name": tool_call.function.name,
                                "input": tool_call.function.arguments,  # This is a JSON string
                                "type": "function",
                            }
                        )

            # Get mapped parameter values (same as Anthropic)
            model_name = self.get_mapped_param_value(
                kwargs, "model_name"
            ) or self.get_mapped_param_value(kwargs, "model")
            raw_system_prompt = self.get_mapped_param_value(
                kwargs, "system_prompt"
            )
            system_prompt, system_prompt_cache_metadata = process_system_prompt(
                raw_system_prompt
            )
            user_prompt = self.get_mapped_param_value(
                kwargs, "chat_messages"
            ) or self.get_mapped_param_value(kwargs, "user_prompt")
            operation_name = self.get_mapped_param_value(
                kwargs, "operation_name"
            )
            max_tokens = self.get_mapped_param_value(kwargs, "max_tokens")
            temperature = self.get_mapped_param_value(kwargs, "temperature")
            tools = self.get_mapped_param_value(kwargs, "tools")

            if tools:
                tool_names = extract_tool_names_from_tools(tools)
            else:
                tool_names = []

            # Calculate cost using provider method (this should work with tokens_data dict)
            cost_details = {}
            if tokens_data and model_name:
                try:
                    cost_details = self.provider.calculate_cost(
                        tokens_data, model_name
                    )
                except ValueError as e:
                    raise e

            # Create tool call metadata from extracted tool calls
            tool_call_metadata = {
                "hasToolCalls": len(tool_calls) > 0,
                "toolCallCount": len(tool_calls),
                "hasToolResults": False,  # SDK response doesn't contain tool results
                "toolResultCount": 0,
            }

            input_messages = []
            input_messages.append({"role": "system", "content": system_prompt})
            # Convert OpenAI messages to Langfuse format
            if isinstance(user_prompt, list):
                for msg in user_prompt:
                    input_messages.append(
                        {
                            "role": msg.get("role", "user"),
                            "content": msg.get("content", ""),
                        }
                    )
            else:
                input_messages.append(
                    {"role": "user", "content": user_prompt or ""}
                )

            generation_data = {
                "model_name": model_name,
                "service_provider": self.provider.name,
                "input": input_messages,
                "output": llm_response,
                "usage": tokens_data,
                "cost_details": cost_details,
                "start_time": start_time,
                "end_time": end_time,
                "tool_call_metadata": tool_call_metadata,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "tool_names": tool_names,
            }

            # Build complete metadata for OpenAI (no cache tokens like Anthropic)
            complete_metadata = {
                "model": model_name,
                "provider": self.provider.name,
                "maxTokens": max_tokens,
                "temperature": temperature,
                "tool": tool_names,
                "timeTaken": (end_time - start_time).total_seconds(),
                "inputTokens": tokens_data.get("prompt_tokens", 0),
                "outputTokens": tokens_data.get("completion_tokens", 0),
                "inputCost": cost_details.get("input", 0.0),
                "outputCost": cost_details.get("output", 0.0),
                "totalCost": cost_details.get("total", 0.0),
                "sdkMode": True,
                "originalResponse": sdk_response,
                **tool_call_metadata,
                **system_prompt_cache_metadata,
            }

            # Add Gemini-specific modality token breakdown if available
            if self.provider.name == "gemini":
                if "prompt_text_tokens" in tokens_data:
                    complete_metadata["promptTextTokens"] = tokens_data[
                        "prompt_text_tokens"
                    ]
                if "prompt_image_tokens" in tokens_data:
                    complete_metadata["promptImageTokens"] = tokens_data[
                        "prompt_image_tokens"
                    ]
                if "completion_text_tokens" in tokens_data:
                    complete_metadata["completionTextTokens"] = tokens_data[
                        "completion_text_tokens"
                    ]
                if "completion_image_tokens" in tokens_data:
                    complete_metadata["completionImageTokens"] = tokens_data[
                        "completion_image_tokens"
                    ]

            # Filter metadata if metadata_config is provided
            filtered_metadata = self.filter_metadata(complete_metadata)

            generation_id = await _LangfuseService.create_generation_for_LLM(
                trace_id,
                generation_data,
                (
                    operation_name.replace("_", " ").title()
                    if operation_name
                    else f"{self.provider.name.capitalize()} Generation"
                ),
                filtered_metadata,
            )

            generation_id_context.set(generation_id)
            return result

        except Exception as e:
            # This is a tracing/decorator error - log it but don't break the function result
            import traceback

            print(f"[LANGFUSE] Error in OpenAI SDK mode tracing: {e}")
            print(traceback.format_exc())
            # Return the original result even if tracing fails
            return result


class LLMStreamingTracer(BaseTracer):
    """
    OOP implementation of LLM streaming tracing with CLEAN SEPARATION logic.

    LOGIC:
    ==========
    - This tracer is used ONLY on the pure LLM streaming service
    - Each call to the service creates ONE focused trace
    - Tool execution happens OUTSIDE the trace (in orchestrator)
    - Each trace focuses purely on LLM interaction
    - Multiple traces for multi-step conversations
    - Supports both streaming and SDK modes based on is_sdk parameter
    """

    def __init__(
        self,
        provider,
        variable_mapping: Optional[Dict[str, str]] = None,
        metadata_config: Optional[List[str]] = None,
        is_sdk: bool = False,
    ):
        super().__init__(provider, variable_mapping, metadata_config)
        self.is_sdk = is_sdk
        if provider.name != "anthropic":
            raise ValueError(
                "Streaming tracing currently only supports Anthropic provider"
            )

    def trace(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute streaming LLM tracing for PURE LLM service calls.

        APPROACH:
        - Each call creates ONE focused trace
        - Only tracks LLM input/output for THIS call
        - Tool calls are noted but not executed here
        - Tool results from previous calls are in input for context
        - Supports both streaming mode (is_sdk=False) and SDK mode (is_sdk=True)

        NEW SDK MODE BEHAVIOR:
        - When is_sdk=True, the function should be an async generator that yields streaming data
        - The decorator will look for special "anthropic_final_message" events in the stream
        - When found, it extracts the final message data and creates the trace
        """
        if self.is_sdk:
            # SDK mode: Handle async generator with anthropic_final_message events
            return self._trace_sdk_streaming_mode(func, *args, **kwargs)
        else:
            # Streaming mode: Handle stream chunks - return async generator
            return self._trace_streaming_mode(func, *args, **kwargs)

    async def _trace_sdk_streaming_mode(self, func: Callable, *args, **kwargs):
        """
        NEW SDK STREAMING MODE: Handle async generator with anthropic_final_message events.

        This method expects the decorated function to be an async generator that:
        1. Yields streaming data from Anthropic SDK (text chunks, events, etc.)
        2. Yields a special event: data: {"type": "anthropic_final_message", "data": final_message_object}
        3. Includes _request_id in the final message for request tracking

        The decorator will:
        - Pass through all streaming data to the client
        - Detect the anthropic_final_message event
        - Extract the final message data and create a trace
        - Continue yielding remaining stream data
        """
        if not self.should_trace():
            async for chunk in func(*args, **kwargs):
                yield chunk
            return

        # Try to get the async generator - if this fails, it's a function error that should be raised
        try:
            generator = func(*args, **kwargs)
        except Exception:
            # This is an error from the decorated function itself - raise it
            raise

        trace_id = request_context.get()
        start_time = datetime.now()
        final_message_data = None

        # Get mapped parameter values - if this fails, it's a decorator error, log it
        try:
            model_name = self.get_mapped_param_value(kwargs, "model_name")
            raw_system_prompt = self.get_mapped_param_value(
                kwargs, "system_prompt"
            )
            system_prompt, system_prompt_cache_metadata = process_system_prompt(
                raw_system_prompt
            )
            user_prompt = self.get_mapped_param_value(kwargs, "chat_messages")
            operation_name = self.get_mapped_param_value(
                kwargs, "operation_name"
            )
            max_tokens = self.get_mapped_param_value(kwargs, "max_tokens")
            temperature = self.get_mapped_param_value(kwargs, "temperature")
            tools = self.get_mapped_param_value(kwargs, "tools")
            if tools:
                tool_names = extract_tool_names_from_tools(tools)
            else:
                tool_names = []

            input_tool_summary = {}
            if user_prompt and isinstance(user_prompt, list):
                input_tool_summary = get_tool_call_summary_from_messages(
                    user_prompt
                )

            tracing_enabled = True
        except Exception as e:
            # This is a decorator/tracing setup error - log it but continue
            print(f"[LANGFUSE] Error setting up tracing parameters: {e}")
            tracing_enabled = False

        try:
            # Process the async generator stream
            async for chunk in generator:
                if tracing_enabled:
                    try:
                        # Check for the special anthropic_final_message event
                        if isinstance(chunk, str) and chunk.startswith(
                            "data: "
                        ):
                            try:
                                chunk_data = json.loads(
                                    chunk[6:]
                                )  # Remove "data: " prefix
                                if (
                                    chunk_data.get("type")
                                    == "anthropic_final_message"
                                ):
                                    # Found the final message event - extract data
                                    final_message_data = chunk_data.get(
                                        "data", {}
                                    )
                                    # Don't yield this special event, just process it
                                    continue
                            except json.JSONDecodeError:
                                # Not a JSON chunk, pass it through
                                pass
                    except Exception as e:
                        # Tracing error while processing chunk - log but continue
                        print(
                            f"[LANGFUSE] Error processing chunk for tracing: {e}"
                        )

                # Always yield the chunk to the client
                yield chunk

            # Process the final message if we found it and tracing is enabled
            if tracing_enabled and final_message_data:
                try:
                    end_time = datetime.now()
                    await self._process_anthropic_final_message(
                        trace_id,
                        final_message_data,
                        model_name,
                        system_prompt,
                        user_prompt,
                        operation_name,
                        max_tokens,
                        temperature,
                        tool_names,
                        input_tool_summary,
                        start_time,
                        end_time,
                        system_prompt_cache_metadata,
                    )
                except Exception as e:
                    # Tracing error while creating trace - log but don't break
                    print(f"[LANGFUSE] Error creating trace: {e}")
            elif tracing_enabled and not final_message_data:
                print(
                    "[LANGFUSE] Warning: No anthropic_final_message event found in SDK streaming mode"
                )

        except Exception:
            # This is an error from the generator iteration (function error) - raise it
            raise

    async def _process_anthropic_final_message(
        self,
        trace_id,
        final_message_data,
        model_name,
        system_prompt,
        user_prompt,
        operation_name,
        max_tokens,
        temperature,
        tool_names,
        input_tool_summary,
        start_time,
        end_time,
        system_prompt_cache_metadata,
    ):
        """Process the anthropic final message and create trace."""
        try:
            # Extract data from the final message (similar to original SDK mode logic)
            usage_data = final_message_data.get("usage", {})
            total_input_tokens = usage_data.get("input_tokens", 0)
            total_output_tokens = usage_data.get("output_tokens", 0)
            cache_creation_input_tokens = usage_data.get(
                "cache_creation_input_tokens", 0
            )
            cache_read_input_tokens = usage_data.get(
                "cache_read_input_tokens", 0
            )

            # Extract response content, tool calls, and "thinking" block
            collected_response = ""
            collected_tool_calls = []
            thinking_block = None

            content = final_message_data.get("content", [])
            if isinstance(content, list):
                for content_block in content:
                    if isinstance(content_block, dict):
                        if content_block.get("type") == "text":
                            collected_response += content_block.get("text", "")
                        elif content_block.get("type") == "tool_use":
                            tool_call = {
                                "id": content_block.get("id", ""),
                                "name": content_block.get("name", ""),
                                "input": content_block.get("input", {}),
                                "type": "tool_use",
                            }
                            collected_tool_calls.append(tool_call)
                        elif content_block.get("type") == "thinking":
                            # Extract the whole thinking block (not just the text)
                            thinking_block = content_block["thinking"]

            # Calculate tokens and cost
            tokens_data = {
                "prompt_tokens": total_input_tokens,
                "completion_tokens": total_output_tokens,
                "total_tokens": total_input_tokens + total_output_tokens,
                "cache_creation_input_tokens": cache_creation_input_tokens,
                "cache_read_input_tokens": cache_read_input_tokens,
            }

            cost_details = {}
            if tokens_data and model_name:
                try:
                    cost_details = self.provider.calculate_cost(
                        tokens_data, model_name
                    )
                except ValueError as e:
                    raise e

            # Create tool call metadata for THIS trace only
            tool_call_metadata = {
                # PRIMARY: Current stream - what THIS LLM call produced
                "currentStreamHasToolCalls": len(collected_tool_calls) > 0,
                "currentStreamToolCallCount": len(collected_tool_calls),
                "currentStreamToolCalls": collected_tool_calls,
                # CONTEXT: Input message context (for reference only)
                "inputContextHasToolCalls": input_tool_summary.get(
                    "has_tool_calls", False
                ),
                "inputContextToolCallCount": input_tool_summary.get(
                    "tool_call_count", 0
                ),
                "inputContextHasToolResults": input_tool_summary.get(
                    "has_tool_results", False
                ),
                "inputContextToolResultCount": input_tool_summary.get(
                    "tool_result_count", 0
                ),
                # LEGACY: For backward compatibility (focused on current stream)
                "hasToolCalls": len(collected_tool_calls) > 0,
                "toolCallCount": len(collected_tool_calls),
                "hasToolResults": input_tool_summary.get(
                    "has_tool_results", False
                ),
                "toolResultCount": input_tool_summary.get(
                    "tool_result_count", 0
                ),
                "toolCalls": collected_tool_calls,
                "toolResults": input_tool_summary.get("tool_results", []),
                # SDK streaming specific metadata
                "sdkMode": True,
                "sdkStreamingMode": True,
                "sdkResponseId": final_message_data.get("id", ""),
                "sdkStopReason": final_message_data.get("stop_reason", ""),
                "requestId": final_message_data.get(
                    "_request_id", ""
                ),  # Include request ID
                "originalResponse": final_message_data,
            }

            # Add the "thinking" block to metadata if present
            if thinking_block is not None:
                tool_call_metadata["anthropicThinkingBlock"] = thinking_block

            await self._create_generation(
                trace_id,
                model_name,
                system_prompt,
                user_prompt,
                operation_name,
                max_tokens,
                temperature,
                tool_names,
                input_tool_summary,
                collected_response,
                tokens_data,
                cost_details,
                tool_call_metadata,
                start_time,
                end_time,
                system_prompt_cache_metadata,
            )

        except Exception as e:
            # This is a tracing/decorator error - log it but don't break the function result
            print(f"[LANGFUSE] Error processing anthropic final message: {e}")

    async def _trace_streaming_mode(self, func: Callable, *args, **kwargs):
        """Handle streaming mode tracing - expects async generator yielding chunks."""
        # Try to get the async generator - if this fails, it's a function error that should be raised
        try:
            generator = func(*args, **kwargs)
        except Exception:
            # This is an error from the decorated function itself - raise it
            raise

        trace_id = request_context.get()
        start_time = datetime.now()
        total_input_tokens = 0
        total_output_tokens = 0
        cache_creation_input_tokens = 0
        cache_read_input_tokens = 0
        collected_response = ""
        collected_tool_calls = []  # Tool calls from CURRENT stream only

        # Get mapped parameter values - if this fails, it's a decorator error, log it
        try:
            model_name = self.get_mapped_param_value(kwargs, "model_name")
            raw_system_prompt = self.get_mapped_param_value(
                kwargs, "system_prompt"
            )
            system_prompt, system_prompt_cache_metadata = process_system_prompt(
                raw_system_prompt
            )
            user_prompt = self.get_mapped_param_value(kwargs, "chat_messages")
            operation_name = self.get_mapped_param_value(
                kwargs, "operation_name"
            )
            max_tokens = self.get_mapped_param_value(kwargs, "max_tokens")
            temperature = self.get_mapped_param_value(kwargs, "temperature")
            tools = self.get_mapped_param_value(kwargs, "tools")
            if tools:
                tool_names = extract_tool_names_from_tools(tools)
            else:
                tool_names = []

            input_tool_summary = {}
            if user_prompt and isinstance(user_prompt, list):
                input_tool_summary = get_tool_call_summary_from_messages(
                    user_prompt
                )

            tracing_enabled = True
        except Exception as e:
            # This is a decorator/tracing setup error - log it but continue
            print(f"[LANGFUSE] Error setting up tracing parameters: {e}")
            tracing_enabled = False

        try:
            # Streaming mode: Original logic for processing stream chunks
            async for response_line in generator:
                if tracing_enabled:
                    try:
                        if response_line.startswith("data: "):
                            response_data = json.loads(response_line[6:])

                            # Handle streaming events
                            if response_data["type"] == "message_start":
                                usage = response_data["message"]["usage"]
                                total_input_tokens = usage.get(
                                    "input_tokens", 0
                                )
                                total_output_tokens = usage.get(
                                    "output_tokens", 0
                                )
                                cache_creation_input_tokens = usage.get(
                                    "cache_creation_input_tokens", 0
                                )
                                cache_read_input_tokens = usage.get(
                                    "cache_read_input_tokens", 0
                                )
                            elif response_data["type"] == "content_block_start":
                                content_block = response_data.get(
                                    "content_block", {}
                                )
                                if content_block.get("type") == "tool_use":
                                    # Track tool calls from THIS stream
                                    tool_call = {
                                        "id": content_block.get("id", ""),
                                        "name": content_block.get("name", ""),
                                        "input": content_block.get("input", {}),
                                        "type": "tool_use",
                                    }
                                    collected_tool_calls.append(tool_call)
                            elif response_data["type"] == "content_block_delta":
                                if (
                                    response_data.get("delta", {}).get("type")
                                    == "text_delta"
                                ):
                                    collected_response += response_data[
                                        "delta"
                                    ]["text"]
                            elif response_data["type"] == "message_delta":
                                if "usage" in response_data:
                                    total_output_tokens += response_data[
                                        "usage"
                                    ].get("output_tokens", 0)
                    except Exception as e:
                        # Tracing error while processing chunk - log but continue
                        print(
                            f"[LANGFUSE] Error processing chunk for tracing: {e}"
                        )

                # Always yield the response to the client
                yield response_line

            # Create trace after streaming completes
            if tracing_enabled:
                try:
                    end_time = datetime.now()

                    # Calculate tokens and cost
                    tokens_data = {
                        "prompt_tokens": total_input_tokens,
                        "completion_tokens": total_output_tokens,
                        "total_tokens": total_input_tokens
                        + total_output_tokens,
                        "cache_creation_input_tokens": cache_creation_input_tokens,
                        "cache_read_input_tokens": cache_read_input_tokens,
                    }

                    cost_details = {}
                    if tokens_data and model_name:
                        try:
                            cost_details = self.provider.calculate_cost(
                                tokens_data, model_name
                            )
                        except ValueError as e:
                            print(f"[LANGFUSE] Error calculating cost: {e}")
                            cost_details = {}

                    # Create FOCUSED tool call metadata for THIS trace only
                    tool_call_metadata = {
                        # PRIMARY: Current stream - what THIS LLM call produced
                        "currentStreamHasToolCalls": len(collected_tool_calls)
                        > 0,
                        "currentStreamToolCallCount": len(collected_tool_calls),
                        "currentStreamToolCalls": collected_tool_calls,
                        # CONTEXT: Input message context (for reference only)
                        "inputContextHasToolCalls": input_tool_summary.get(
                            "has_tool_calls", False
                        ),
                        "inputContextToolCallCount": input_tool_summary.get(
                            "tool_call_count", 0
                        ),
                        "inputContextHasToolResults": input_tool_summary.get(
                            "has_tool_results", False
                        ),
                        "inputContextToolResultCount": input_tool_summary.get(
                            "tool_result_count", 0
                        ),
                        # LEGACY: For backward compatibility (focused on current stream)
                        "hasToolCalls": len(collected_tool_calls) > 0,
                        "toolCallCount": len(collected_tool_calls),
                        "hasToolResults": input_tool_summary.get(
                            "has_tool_results", False
                        ),
                        "toolResultCount": input_tool_summary.get(
                            "tool_result_count", 0
                        ),
                        "toolCalls": collected_tool_calls,
                        "toolResults": input_tool_summary.get(
                            "tool_results", []
                        ),
                        # Streaming specific metadata
                        "sdkMode": False,
                    }

                    await self._create_generation(
                        trace_id,
                        model_name,
                        system_prompt,
                        user_prompt,
                        operation_name,
                        max_tokens,
                        temperature,
                        tool_names,
                        input_tool_summary,
                        collected_response,
                        tokens_data,
                        cost_details,
                        tool_call_metadata,
                        start_time,
                        end_time,
                        system_prompt_cache_metadata={},
                    )

                except Exception as e:
                    # Tracing error while creating trace - log but don't break
                    print(f"[LANGFUSE] Error creating trace: {e}")

        except Exception:
            # This is an error from the generator iteration (function error) - raise it
            raise

    async def _create_generation(
        self,
        trace_id,
        model_name,
        system_prompt,
        user_prompt,
        operation_name,
        max_tokens,
        temperature,
        tool_names,
        input_tool_summary,
        collected_response,
        tokens_data,
        cost_details,
        tool_call_metadata,
        start_time,
        end_time,
        system_prompt_cache_metadata={},
    ):
        """Common method to create generation for both SDK and streaming modes."""
        # Create input messages for trace
        input_messages = []
        input_messages.append({"role": "system", "content": system_prompt})

        # Convert messages to Langfuse format
        if self.provider.name == "anthropic":
            input_messages += convert_anthropic_messages_to_langfuse_format(
                user_prompt
            )
        elif self.provider.name == "groq":
            input_messages += convert_groq_messages_to_langfuse_format(
                user_prompt
            )
        else:
            input_messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]

        generation_data = {
            "model_name": model_name,
            "service_provider": self.provider.name,
            "input": input_messages,
            "output": collected_response,
            "usage": tokens_data,
            "cost_details": cost_details,
            "start_time": start_time,
            "end_time": end_time,
            "tool_call_metadata": tool_call_metadata,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "tool_names": tool_names,
        }

        # Build complete metadata
        complete_metadata = {
            "model": model_name,
            "provider": self.provider.name,
            "maxTokens": max_tokens,
            "temperature": temperature,
            "tool": tool_names,
            "timeTaken": (end_time - start_time).total_seconds(),
            "inputTokens": tokens_data.get("prompt_tokens", 0),
            "outputTokens": tokens_data.get("completion_tokens", 0),
            "cacheCreationInputTokens": tokens_data.get(
                "cache_creation_input_tokens", 0
            ),
            "cacheReadInputTokens": tokens_data.get(
                "cache_read_input_tokens", 0
            ),
            "inputCost": cost_details.get("input", 0.0),
            "outputCost": cost_details.get("output", 0.0),
            "cacheCreationCost": cost_details.get("cache_creation", 0.0),
            "cacheReadCost": cost_details.get("cache_read", 0.0),
            "totalCost": cost_details.get("total", 0.0),
            **tool_call_metadata,
            **system_prompt_cache_metadata,
        }

        # Add Gemini-specific modality token breakdown if available
        if self.provider.name == "gemini":
            if "prompt_text_tokens" in tokens_data:
                complete_metadata["promptTextTokens"] = tokens_data[
                    "prompt_text_tokens"
                ]
            if "prompt_image_tokens" in tokens_data:
                complete_metadata["promptImageTokens"] = tokens_data[
                    "prompt_image_tokens"
                ]
            if "completion_text_tokens" in tokens_data:
                complete_metadata["completionTextTokens"] = tokens_data[
                    "completion_text_tokens"
                ]
            if "completion_image_tokens" in tokens_data:
                complete_metadata["completionImageTokens"] = tokens_data[
                    "completion_image_tokens"
                ]

        # Filter metadata if metadata_config is provided
        filtered_metadata = self.filter_metadata(complete_metadata)

        generation_id = await _LangfuseService.create_generation_for_LLM(
            trace_id,
            generation_data,
            (
                operation_name.replace("_", " ").title()
                if operation_name
                else f"{self.provider.name.capitalize()} Generation"
            ),
            filtered_metadata,
        )

        generation_id_context.set(generation_id)
