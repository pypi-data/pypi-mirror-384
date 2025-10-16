# ObserveLLM

A powerful observability library for AI/ML applications that provides comprehensive tracing and monitoring capabilities using Langfuse.

## Installation

Install the package from PyPI using:

```bash
pip install observeLLM
```

Note: It is recommended to use the latest version for optimal performance.

## Quick Start

### 1. Initialize Langfuse Client

First, initialize the Langfuse client at your application startup:

```python
from observe_traces import LangfuseInitializer, request_context, trace_api_call
from observe_traces import llm_tracing, llm_streaming_tracing, embedding_tracing, vectordb_tracing, reranking_tracing, general_tracing
from observe_traces import ObservabilityService

# Initialize Langfuse client
LangfuseInitializer.initialize(
    langfuse_public_key='your_langfuse_public_key',
    langfuse_secret_key='your_langfuse_secret_key',
    langfuse_host='your_host_url',  # e.g., 'http://localhost:3000'
    release='app_version',          # e.g., '1.0.0'
    environment='your_environment'  # e.g., 'development', 'production'
)

# Optional: Close Langfuse client when shutting down
LangfuseInitializer.close()
```

### 2. FastAPI Middleware Setup

Add the unified middleware to your FastAPI application in `main.py` or your entry point:

```python
from fastapi import FastAPI, Request
from observe_traces import unified_middleware, trace_api_call

app = FastAPI()

@app.middleware("http")
async def set_request_context_middleware(request: Request, call_next):
    session_id = request.headers.get("X-Request-ID")
    
    # Capture request body for trace input (optional)
    body = None
    if request.method in ["POST", "PUT", "PATCH"]:
        try:
            body = await request.json()
        except:
            # If body can't be parsed as JSON, you can capture it as text or skip
            pass

    metadata = {
        "sessionId": session_id,
        "environment": "development",
        "serviceName": "observeLLM",
        "apiEndpoint": request.url.path,
        "user": request.headers.get("X-User-Email"),
        **(body or {}),
    }
    
    # Optional: Define custom route names
    route_mapping = {
        "/api/chat": "Chat Generation",
        "/api/embeddings": "Text Embedding",
        "/api/rerank": "Document Reranking"
    }
    
    # Optional: Define tags for categorization and filtering
    tag_mapping = {
        "/api/chat": ["production", "llm", "chat"],
        "/api/embeddings": ["production", "embedding", "search"],
        "/api/rerank": ["production", "reranking", "search"],
        "/api/health": ["monitoring", "health"]
    }
    
    # Optional: Include/exclude routes from tracing
    include_routes = ["/api/chat", "/api/embeddings", "/api/rerank"]
    exclude_routes = ["/health", "/metrics", "/docs"]
    
    # Prepare input data for trace (can be request body, query params, or custom data)
    trace_input = {
        "method": request.method,
        "path": request.url.path,
        "query_params": dict(request.query_params),
        "headers": dict(request.headers),
        "body": body
    }
    
    return await unified_middleware(
        request, 
        call_next, 
        metadata=metadata,
        route_mapping=route_mapping,
        tag_mapping=tag_mapping,
        include_routes=include_routes,
        exclude_routes=exclude_routes,
        input=trace_input
    )
```

**New Input Capture Feature:**
- `input`: Captures input data for traces (can be any JSON object)
- Useful for tracking request payloads, query parameters, headers, etc.
- Helps with debugging and understanding what data was provided to each trace
- Example: `{"method": "POST", "body": {"query": "Hello"}, "headers": {...}}`

**Enhanced Features:**
- `tag_mapping`: Maps route paths to lists of tags for categorization
- Tags help organize and filter traces in the Langfuse UI
- Useful for grouping traces by environment, service type, or functionality
- Example: `{"/api/chat": ["production", "llm"], "/api/embeddings": ["production", "embedding"]}`

## Usage Methods

ObserveLLM provides two ways to use the tracing decorators:

### Method 1: Direct Decorator Functions

Use the imported decorator functions directly:

```python
from observe_traces import llm_tracing, embedding_tracing, vectordb_tracing, reranking_tracing

@llm_tracing(provider='openai')
async def my_llm_function():
    # Your implementation
    pass
```

### Method 2: ObservabilityService Class

Create an `ObservabilityService` instance and use its methods:

```python
from observe_traces import ObservabilityService

# Create service instance
observability_service = ObservabilityService()

# Use as decorator methods
@observability_service.llm_tracing(provider='openai')
async def my_llm_function():
    # Your implementation
    pass
```

Both methods provide identical functionality and can be used interchangeably.

## Variable Mapping

All tracing decorators support an optional `variable_mapping` parameter that allows you to map the expected parameter names to your actual function parameter names. This is useful when your function parameters don't match the decorator's expected names.

**Important**: The mapping direction is `expected_parameter_name: your_parameter_name`

### LLM Tracing Expected Parameters

For both `llm_tracing` and `llm_streaming_tracing` decorators, the following parameters are expected:

- `model_name` (required) - The model name/identifier (fallback: `model`)
- `system_prompt` (optional) - System instructions for the model
- `chat_messages` (required) - The conversation messages/user prompt (fallback: `user_prompt`)
- `operation_name` (optional) - Custom name for the operation (used in trace naming)
- `max_tokens` (optional) - Maximum tokens to generate
- `temperature` (optional) - Sampling temperature
- `tools` (optional) - Available tools/functions for the model

**Additional decorator parameters:**
- `metadata_config` (optional) - List of metadata keys to include in traces. If None, includes all metadata.
- `is_sdk` (optional) - Boolean indicating SDK mode (True) vs standard mode (False, default). Supported for both `llm_tracing` and `llm_streaming_tracing` decorators.

**Note**: The decorator will automatically try fallback parameter names if the primary ones are not found. For example, if `model_name` is not provided, it will look for `model`. If `chat_messages` is not found, it will look for `user_prompt`.

```python
from observe_traces import ObservabilityService

observability_service = ObservabilityService()

@observability_service.llm_tracing(
    provider='openai',
    variable_mapping={
        'model_name': 'model',           # Maps decorator's 'model_name' to your 'model' parameter
        'chat_messages': 'user_prompt',  # Maps decorator's 'chat_messages' to your 'user_prompt' parameter
        'system_prompt': 'system_msg',   # Maps decorator's 'system_prompt' to your 'system_msg' parameter
        'operation_name': 'task_name',   # Maps decorator's 'operation_name' to your 'task_name' parameter
        'max_tokens': 'max_length',      # Maps decorator's 'max_tokens' to your 'max_length' parameter
        'temperature': 'temp',           # Maps decorator's 'temperature' to your 'temp' parameter
        'tools': 'available_tools'       # Maps decorator's 'tools' to your 'available_tools' parameter
    }
)
async def my_custom_llm_function(model, system_msg, user_prompt, task_name=None, max_length=None, temp=None, available_tools=None, **kwargs):
    # Your implementation here
    pass

# Example for streaming LLM with metadata filtering
@observability_service.llm_streaming_tracing(
    provider='anthropic',
    variable_mapping={
        'model_name': 'model',
        'chat_messages': 'messages',
        'system_prompt': 'system',
        'operation_name': 'stream_name',
        'max_tokens': 'max_output_tokens',
        'temperature': 'temp_setting',
        'tools': 'function_tools'
    },
    metadata_config=['model', 'provider', 'timeTaken', 'totalCost'],
    is_sdk=False
)
async def my_custom_streaming_function(model, system, messages, stream_name=None, max_output_tokens=None, temp_setting=None, function_tools=None, **kwargs):
    # Your streaming implementation here with filtered metadata
    pass
```

**Note**: If you don't provide variable mapping, your function parameters must match the expected parameter names exactly. For example:

```python
@observability_service.llm_tracing(provider='openai')
async def standard_llm_function(model_name, system_prompt, chat_messages, operation_name=None, max_tokens=None, temperature=None, tools=None, **kwargs):
    # Function parameters match expected names exactly
    pass
```

### Other Decorator Mappings

The mapping works for all decorator types:
- **LLM Tracing**: Maps `model_name`, `system_prompt`, `chat_messages`, `operation_name`, `max_tokens`, `temperature`, `tools`
- **Embedding Tracing**: Maps `model_name`, `inputs`, `texts`, etc.
- **Vector DB Tracing**: Maps `namespace`, `query`, `index_host`, `top_k`, etc.
- **Reranking Tracing**: Maps `model_name`, `query`, `documents`, `top_n`, etc.

## Tracing Decorators

ObserveLLM provides six powerful decorators and utility functions to enable comprehensive tracing for different AI/ML components:

### 1. LLM Tracing

```python
from observe_traces import llm_tracing
# OR
from observe_traces import ObservabilityService
observability_service = ObservabilityService()

@llm_tracing(provider='openai')  # Direct function
# OR
@observability_service.llm_tracing(provider='openai')  # Service method
async def llm_api_calling_function(
    model_name: str,             # Required: e.g., 'gpt-3.5-turbo'
    system_prompt: str,          # Optional: System instructions
    chat_messages: list,         # Required: Conversation history
    operation_name: str = None,  # Optional: Custom operation name for tracing
    max_tokens: int = None,      # Optional: Maximum tokens to generate
    temperature: float = None,   # Optional: Sampling temperature
    tools: list = None,          # Optional: Available tools/functions
    **kwargs                     # Additional parameters
):
    # Your LLM API calling logic here
    # Returns either:
    # 1. Tuple of (response_data, raw_response)
    # 2. Raw response object

# Example with metadata filtering
@llm_tracing(
    provider='openai',
    metadata_config=['maxTokens', 'temperature', 'totalCost']  # Only include specific metadata
)
async def cost_focused_llm_function(model_name, chat_messages, **kwargs):
    # Only 'maxTokens', 'temperature', and 'totalCost' will be included in trace metadata
    pass

# SDK Mode Support (OpenAI and Anthropic)
@llm_tracing(provider='openai', is_sdk=True)  # SDK mode for OpenAI
async def openai_sdk_function(model_name, chat_messages, **kwargs):
    # Use OpenAI SDK directly - returns complete SDK response object
    from openai import AsyncOpenAI
    client = AsyncOpenAI()
    response = await client.chat.completions.create(
        model=model_name,
        messages=chat_messages,
        tools=kwargs.get('tools', [])
    )
    return response  # Return SDK response object directly

@llm_tracing(provider='anthropic', is_sdk=True)  # SDK mode for Anthropic  
async def anthropic_sdk_function(model_name, chat_messages, **kwargs):
    # Use Anthropic SDK directly - returns complete SDK response object
    from anthropic import AsyncAnthropic
    client = AsyncAnthropic()
    response = await client.messages.create(
        model=model_name,
        messages=chat_messages,
        tools=kwargs.get('tools', [])
    )
    return response  # Return SDK response object directly

@llm_tracing(provider='openai', is_sdk=False)  # Standard mode (default)
async def openai_standard_function(model_name, chat_messages, **kwargs):
    # Use raw HTTP requests - returns tuple (response_text, raw_json_response)
    import httpx
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.openai.com/v1/chat/completions",
            json={"model": model_name, "messages": chat_messages},
            headers={"Authorization": f"Bearer {api_key}"}
        )
        raw_json = response.json()
        text = raw_json["choices"][0]["message"]["content"]
    return text, raw_json  # Return tuple
```

**`is_sdk` Parameter for LLM Tracing:**

The `is_sdk` parameter determines how the decorator processes function returns:

- **`is_sdk=False` (default)**: Standard mode - expects raw HTTP API responses, typically returned as tuple `(response_text, raw_json_response)`
- **`is_sdk=True`**: SDK mode - expects complete SDK response objects (e.g., OpenAI `ChatCompletion` or Anthropic `Message` objects)

**SDK Mode Benefits:**
- Direct extraction of token usage, tool calls, and metadata from SDK objects
- Enhanced tool call support with comprehensive metadata
- Simplified integration with official SDKs
- Automatic handling of complex response structures

Supported LLM Providers:

- OpenAI (GPT-3.5, GPT-4, GPT-4o, etc.) - SDK mode supported
- Anthropic (Claude models) - SDK mode supported  
- Groq
- Custom providers can be added using `register_provider()`

### 2. LLM Streaming Tracing

```python
from observe_traces import llm_streaming_tracing
# OR
from observe_traces import ObservabilityService
observability_service = ObservabilityService()
import json

@llm_streaming_tracing(provider='anthropic', is_sdk=False)  # Direct function
# OR
@observability_service.llm_streaming_tracing(provider='anthropic', is_sdk=False)  # Service method
async def llm_streaming_function(
    model_name: str,             # Required: e.g., 'claude-3-opus-20240229'
    system_prompt: str,          # Optional: System instructions
    chat_messages: list,         # Required: Conversation history
    operation_name: str = None,  # Optional: Custom operation name for tracing
    max_tokens: int = None,      # Optional: Maximum tokens to generate
    temperature: float = None,   # Optional: Sampling temperature
    tools: list = None,          # Optional: Available tools/functions
    **kwargs                     # Additional parameters
):
    # Your streaming LLM API calling logic here
    # Should be an async generator that yields specific formatted lines:

    # 1. For streaming response chunks:
    #    yield f"data: {json.dumps({'type': 'data', 'data': chunk_text})}"
    #    Example:
    #    yield 'data: {"type": "data", "data": "Hello"}'

    # 2. For token usage information:
    #    yield f"tokens: {json.dumps({'data': {'input': input_tokens, 'output': output_tokens}})}"
    #    Example:
    #    yield 'tokens: {"data": {"input": 10, "output": 5}}'

    # 3. Any other lines that should be passed through unchanged

    # The decorator will:
    # - Collect all response chunks to build the complete response
    # - Track token usage throughout the stream
    # - Calculate costs based on token usage
    # - Create a trace in Langfuse with the complete response and metrics

# SDK Mode for Complete Response Objects
@llm_streaming_tracing(provider='anthropic', is_sdk=True)
async def llm_sdk_function(
    model_name: str,
    chat_messages: list,
    **kwargs
):
    # Your LLM SDK calling logic here that returns a complete response object
    # Example SDK response structure:
    # {
    #     "id": "msg_01...",
    #     "content": [
    #         {"type": "text", "text": "Response content"},
    #         {"type": "tool_use", "id": "toolu_01...", "name": "tool_name", "input": {...}}
    #     ],
    #     "usage": {"input_tokens": 10, "output_tokens": 20},
    #     "stop_reason": "end_turn"
    # }
    return complete_response_object

# Streaming with metadata filtering
@llm_streaming_tracing(
    provider='anthropic',
    is_sdk=False,
    metadata_config=['provider', 'model', 'totalCost', 'hasToolCalls']
)
async def focused_streaming_function(model_name, chat_messages, **kwargs):
    # Only specified metadata fields will be included in the trace
    async for chunk in streaming_api_call():
        yield chunk
```

**is_sdk Parameter:**

The `is_sdk` parameter determines how the decorator handles the function's return value:

- **`is_sdk=False` (default)**: Streaming mode - expects an async generator that yields formatted chunks
- **`is_sdk=True`**: SDK mode - expects an async generator that yields streaming data and special final message events

**Streaming Mode (`is_sdk=False`):**
- Function must be an async generator yielding chunks
- Processes streaming events in real-time
- Collects chunks to build complete response
- Parses token usage from streaming events

**SDK Mode (`is_sdk=True`):**
- Function must be an async generator that yields streaming data in real-time
- Yields streaming text chunks during the LLM response
- Yields a special `anthropic_final_message` event at the end with complete response data
- The decorator automatically detects this special event and extracts trace data from it
- Combines real-time streaming with comprehensive tracing

### SDK Mode Implementation Example

```python
import json
from anthropic import AsyncAnthropic

@llm_streaming_tracing(provider='anthropic', is_sdk=True)
async def sdk_streaming_function(model_name, chat_messages, system_prompt=None, **kwargs):
    """
    SDK Mode function that yields streaming data and final message for tracing.
    
    This function:
    1. Streams text chunks in real-time using the Anthropic SDK
    2. Yields a special anthropic_final_message event with complete response data
    3. The decorator automatically processes this event for comprehensive tracing
    """
    client = AsyncAnthropic(api_key="your-api-key")
    
    try:
        # Stream the response using Anthropic SDK
        async with client.messages.stream(
            model=model_name,
            max_tokens=kwargs.get('max_tokens', 1024),
            system=system_prompt,
            messages=chat_messages,
            temperature=kwargs.get('temperature', 0.7),
            tools=kwargs.get('tools', [])  # Include tools if provided
        ) as stream:
            
            # Yield streaming text chunks in real-time
            async for text in stream.text_stream:
                yield f"data: {json.dumps({'type': 'text_chunk', 'text': text})}\n\n"
            
            # Get the final message with complete response data
            final_message = await stream.get_final_message()
            
            # Convert to dict for the special event
            final_message_dict = final_message.model_dump()
            
            # Yield the special anthropic_final_message event
            # The decorator will detect this and extract tracing data
            yield f"data: {json.dumps({'type': 'anthropic_final_message', 'data': final_message_dict})}\n\n"
            
            # Optional: yield completion event
            yield f"data: {json.dumps({'type': 'stream_complete', 'message': 'SDK streaming completed'})}\n\n"
            
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

# Usage in FastAPI endpoint
@app.post("/stream/sdk-mode")
async def stream_with_sdk_mode(request: StreamingRequest):
    async def generate():
        async for chunk in sdk_streaming_function(
            model_name=request.model,
            system_prompt=request.system_prompt,
            chat_messages=[{"role": msg.role, "content": msg.content} for msg in request.messages],
            max_tokens=request.max_tokens,
            temperature=0.7,
            tools=[{"name": "weather", "description": "Get weather info"}]  # Optional tools
        ):
            yield chunk

    return StreamingResponse(
        generate(),
        media_type="text/plain",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )
```

**Key Benefits of SDK Mode (`is_sdk=True`):**
- **Real-time streaming**: Users see text appearing as it's generated
- **Comprehensive tracing**: Complete response data, token usage, costs, and tool calls are captured
- **Tool call support**: Handles complex responses with tool calls and multiple content blocks
- **Error handling**: Proper error propagation while maintaining streaming capability
- **Automatic processing**: The decorator handles trace creation from the final message event


## Metadata Configuration

All tracing decorators support an optional `metadata_config` parameter that allows you to control which metadata fields are included in your traces. This feature provides fine-grained control over trace payloads and helps focus on specific metrics.

### Usage

```python
# Include only specific metadata fields
@llm_tracing(provider='openai', metadata_config=['maxTokens', 'temperature', 'totalCost'])
async def focused_llm_function(model_name, chat_messages, **kwargs):
    pass

# Include all metadata (default behavior)
@llm_tracing(provider='openai')  # metadata_config=None
async def full_metadata_function(model_name, chat_messages, **kwargs):
    pass

# Include no metadata
@llm_tracing(provider='openai', metadata_config=[])
async def minimal_metadata_function(model_name, chat_messages, **kwargs):
    pass
```

### Available Metadata Fields

**LLM Tracing (`llm_tracing` and `llm_streaming_tracing`):**
- `model` - Model name/identifier
- `provider` - LLM provider name
- `maxTokens` - Maximum tokens to generate
- `temperature` - Sampling temperature
- `tool` - Available tools/functions
- `timeTaken` - Response time in seconds
- `inputTokens` - Number of input tokens
- `outputTokens` - Number of output tokens
- `inputCost` - Cost for input tokens
- `outputCost` - Cost for output tokens
- `totalCost` - Total cost for the request
- `hasToolCalls` - Whether tool calls were made
- `toolCallCount` - Number of tool calls
- `sdkMode` - Whether SDK mode was used (streaming only)
- `currentStreamHasToolCalls` - Tool calls in current stream (streaming only)
- `currentStreamToolCallCount` - Tool call count in current stream (streaming only)
- `originalResponse` - Full raw response from the LLM, use this field wisely
and many more.....

**Embedding Tracing (`embedding_tracing`):**
- `provider` - Embedding provider name
- `model_name` - Model name/identifier
- `input count` - Number of input texts
- `cost` - Total cost for embeddings
- `token usage` - Number of tokens used
- `price` - Detailed pricing information
- `embedding_dimensions` - Dimensionality of embeddings
- `timestamp` - Timestamp of the operation

**Vector DB Tracing (`vectordb_tracing`):**
- `operation_type` - Type of operation (read/write)
- `provider` - Vector DB provider name
- `cost` - Operation cost
- `read_units` - Number of read units consumed
- `index_host` - Vector database host
- `namespace` - Vector database namespace
- `top_k` - Number of results requested (read operations)
- `upserted_vectors` - Number of vectors upserted (write operations)

**Reranking Tracing (`reranking_tracing`):**
- `provider` - Reranking provider name
- `model_name` - Model name/identifier
- `output_count` - Number of documents processed
- `cost` - Total cost for reranking
- `token usage` - Number of tokens used
- `timestamp` - Timestamp of the operation
- `top_n` - Number of top results requested

### Common Use Cases

```python
# Cost tracking focus
@llm_tracing(
    provider='openai',
    metadata_config=['inputCost', 'outputCost', 'totalCost', 'inputTokens', 'outputTokens']
)
async def cost_monitoring_function(model_name, chat_messages, **kwargs):
    pass

# Performance tracking focus
@llm_tracing(
    provider='anthropic',
    metadata_config=['timeTaken', 'inputTokens', 'outputTokens', 'model']
)
async def performance_monitoring_function(model_name, chat_messages, **kwargs):
    pass

# Tool usage tracking
@llm_streaming_tracing(
    provider='anthropic',
    metadata_config=['hasToolCalls', 'toolCallCount', 'currentStreamHasToolCalls', 'tool']
)
async def tool_monitoring_function(model_name, chat_messages, tools, **kwargs):
    pass

# Minimal metadata for compliance
@embedding_tracing(
    provider='openai',
    metadata_config=['provider', 'model_name']
)
async def compliance_focused_embedding(model_name, inputs, **kwargs):
    pass
```

### Benefits

- **Reduced payload size**: Include only necessary metadata to minimize trace size
- **Focused monitoring**: Track specific metrics relevant to your use case
- **Performance optimization**: Smaller payloads improve query and dashboard performance
- **Compliance support**: Exclude sensitive metadata fields when required
- **Cost optimization**: Reduce storage and bandwidth costs for traces

### 3. Embedding Tracing

```python
from observe_traces import embedding_tracing
# OR
from observe_traces import ObservabilityService
observability_service = ObservabilityService()

@embedding_tracing(provider='openai')  # Direct function
# OR
@observability_service.embedding_tracing(provider='openai')  # Service method
async def embedding_generation_function(
    model_name: str,            # e.g., 'text-embedding-ada-002'
    inputs: list,               # List of texts to embed
    **kwargs                    # Additional parameters
):
    # Your embedding API calling logic here
    # Returns either:
    # 1. Tuple of (embeddings, raw_response)
    # 2. Raw response object
```

Supported Embedding Providers:

- OpenAI
- Pinecone
- Cohere
- Jina
- VoyageAI
- Custom providers can be added using `register_embedding_provider()`

### 4. Vector Database Tracing

```python
from observe_traces import vectordb_tracing
# OR
from observe_traces import ObservabilityService
observability_service = ObservabilityService()

# For write operations
@vectordb_tracing(provider='pinecone', operation_type='write')  # Direct function
# OR
@observability_service.vectordb_tracing(provider='pinecone', operation_type='write')  # Service method
async def vectordb_write_function(
    index_host: str,
    vectors: list,
    namespace: str
):
    # Your vector DB write logic here
    # Returns raw response object

# For read operations
@vectordb_tracing(provider='pinecone', operation_type='read')  # Direct function
# OR
@observability_service.vectordb_tracing(provider='pinecone', operation_type='read')  # Service method
async def vectordb_read_function(
    index_host: str,
    namespace: str,
    top_k: int,
    query: str,
    query_vector_embeds: list,
    query_sparse_embeds: dict = None,
    include_metadata: bool = True,
    filter_dict: dict = None
):
    # Your vector DB read logic here
    # Returns raw response object
```

Supported Vector DB Providers:

- Pinecone
- Custom providers can be added by extending the provider configurations

### 5. API Call Tracing

```python
from observe_traces import trace_api_call
from fastapi import Request

@app.get("/some-endpoint")
async def example_endpoint(request: Request):
    # Your API logic here
    input_data = {"param1": "value1", "param2": "value2"}

    # Perform some operation
    result = some_function(input_data)

    # Log the API call within the request trace
    span_id = trace_api_call(
        request=request,
        name="Example API Call",
        input_data=input_data,
        output_data=result,
        metadata={"additional_info": "some value"}
    )

    return result
```

This function allows you to create spans within existing traces to track API calls with:

- Complete input/output data
- Custom metadata
- Integration with the request tracing system

### 6. Reranking Tracing

```python
from observe_traces import reranking_tracing
# OR
from observe_traces import ObservabilityService
observability_service = ObservabilityService()

@reranking_tracing(provider='cohere')  # Direct function
# OR
@observability_service.reranking_tracing(provider='cohere')  # Service method
async def reranking_function(
    model_name: str,
    query: str,
    documents: list,
    top_n: int,
    **kwargs
):
    # Your reranking API calling logic here
    # Returns either:
    # 1. Tuple of (rerank_results, raw_response)
    # 2. Raw response object
```

Supported Reranking Providers:

- Cohere
- Pinecone
- Jina
- VoyageAI
- Custom providers can be added using `register_reranking_provider()`

### 6. General Tracing

```python
from observe_traces import general_tracing
# OR
from observe_traces import ObservabilityService
observability_service = ObservabilityService()

@general_tracing()  # Direct function
# OR
@observability_service.general_tracing()  # Service method
async def any_function(
    param1: Any,                # Any function parameters
    param2: Any,                # The decorator is completely agnostic
    **kwargs                    # Additional parameters
):
    # Your function logic here
    # Returns any value or None
```

The `general_tracing` decorator is a **powerful, agnostic tracing solution** that can trace any Python function regardless of its purpose. It automatically captures:

- Function arguments as input
- Return values as output (or captured results for functions without return values)
- Execution timing and metadata
- **Parent-child relationships for nested function calls**
- Error handling and exception information

**Key Features:**

#### **Case 1: Normal Functions with Return Values**
```python
from observe_traces import general_tracing

@general_tracing()
async def process_data(data: dict, operation: str) -> dict:
    """Function that returns a result."""
    processed = {"operation": operation, "result": data["value"] * 2}
    return processed

# Usage in an endpoint
@app.post("/process")
async def process_endpoint(request: ProcessRequest):
    result = await process_data(request.data, "multiply")
    return {"success": True, "result": result}
```

#### **Case 2: Functions Without Return Values (using capture_result)**
```python
from observe_traces import general_tracing, capture_result

@general_tracing()
async def log_operation(user_id: str, action: str) -> None:
    """Function that doesn't return anything but captures results."""
    log_entry = {
        "user_id": user_id,
        "action": action,
        "timestamp": datetime.now().isoformat(),
        "status": "completed"
    }
    
    # Store in database (no return value)
    database.insert_log(log_entry)
    
    # Capture the result for tracing
    capture_result(log_entry)

# Usage in an endpoint
@app.post("/log")
async def log_endpoint(request: LogRequest):
    await log_operation(request.user_id, request.action)
    return {"success": True, "message": "Action logged"}
```

#### **Case 3: Custom Span Names**
```python
@general_tracing(name="Data Processing Pipeline")
async def complex_data_processing(input_data: list) -> dict:
    """Function with custom span name instead of function name."""
    # Your processing logic
    return {"processed_count": len(input_data)}
```

#### **Case 4: Metadata Filtering**
```python
@general_tracing(metadata_config=["functionName", "timeTaken", "hasReturn", "argumentCount"])
async def optimized_function(large_data: dict) -> dict:
    """Function with filtered metadata to reduce trace payload size."""
    # Only specified metadata fields will be included in the trace
    return {"status": "processed"}
```

**Available Metadata Fields:**
- `functionName` - Name of the traced function
- `timeTaken` - Execution time in seconds
- `hasReturn` - Whether function returns a value
- `hasCapturedResult` - Whether capture_result() was used
- `argumentCount` - Number of function arguments
- `isAsync` - Whether function is async
- `module` - Function's module name
- `hasError` - Whether an error occurred (error cases only)
- `errorType` - Type of error (error cases only)

#### **Case 5: Nested Functions (Parent-Child Relationships)**
```python
@general_tracing(name="Main Workflow")
async def main_workflow(task_id: str) -> dict:
    """Parent function that calls multiple child functions."""
    
    # Step 1: Validate input
    validation_result = await validate_input(task_id)
    
    # Step 2: Process data
    processing_result = await process_task_data(task_id, validation_result)
    
    # Step 3: Generate report
    await generate_task_report(task_id, processing_result)
    
    return {
        "task_id": task_id,
        "status": "completed",
        "validation": validation_result,
        "processing": processing_result
    }

@general_tracing(name="Input Validation")
async def validate_input(task_id: str) -> dict:
    """Child function - automatically nested under parent span."""
    return {"task_id": task_id, "valid": True}

@general_tracing(name="Data Processing")
async def process_task_data(task_id: str, validation: dict) -> dict:
    """Child function - automatically nested under parent span."""
    return {"task_id": task_id, "processed_items": 42}

@general_tracing(name="Report Generation")
async def generate_task_report(task_id: str, data: dict) -> None:
    """Child function without return value."""
    report = {"task_id": task_id, "summary": data, "generated_at": datetime.now()}
    capture_result(report)
```

This creates a **hierarchical trace structure** in Langfuse:
```
📊 Trace: Main Workflow
├── 🟦 Main Workflow (parent span)
│   ├── 🟦 Input Validation (child span)
│   ├── 🟦 Data Processing (child span)
│   └── 🟦 Report Generation (child span)
```

#### **Case 6: ObservabilityService Class Usage**
```python
from observe_traces import ObservabilityService

# Create service instance
observability_service = ObservabilityService()

@observability_service.general_tracing(name="Service Method")
async def service_function(data: list) -> dict:
    """Using ObservabilityService instead of direct decorator."""
    processed = [item * 2 for item in data]
    return {"processed": processed, "count": len(processed)}
```

#### **Case 7: Error Handling**
```python
@general_tracing(name="Error Prone Function")
async def risky_operation(data: dict) -> dict:
    """Function that might throw errors - automatically traced."""
    if not data.get("valid"):
        raise ValueError("Invalid data provided")
    
    return {"status": "success", "data": data}

# Errors are automatically captured in span metadata and output
```

**Complete FastAPI Example:**

```python
from fastapi import FastAPI, Request
from observe_traces import (
    LangfuseInitializer, 
    general_tracing, 
    capture_result, 
    unified_middleware
)

app = FastAPI()

# Initialize Langfuse
LangfuseInitializer.initialize(
    langfuse_public_key="your_key",
    langfuse_secret_key="your_secret", 
    langfuse_host="your_host"
)

# Add middleware for tracing context
@app.middleware("http")
async def tracing_middleware(request: Request, call_next):
    metadata = {
        "sessionId": request.headers.get("X-Session-ID", "default"),
        "user": request.headers.get("X-User-Email", "anonymous"),
        "environment": "production"
    }
    return await unified_middleware(request, call_next, metadata=metadata)

# Traced business logic functions
@general_tracing(name="Order Validation")
async def validate_order(order_data: dict) -> dict:
    # Validation logic
    return {"valid": True, "order_id": order_data["id"]}

@general_tracing(name="Payment Processing")
async def process_payment(order_id: str, amount: float) -> dict:
    # Payment logic
    return {"transaction_id": "txn_123", "status": "completed"}

@general_tracing(name="Inventory Update")
async def update_inventory(order_data: dict) -> None:
    # Inventory logic (no return value)
    inventory_update = {
        "items_updated": len(order_data["items"]),
        "timestamp": datetime.now().isoformat()
    }
    capture_result(inventory_update)

@general_tracing(name="Complete Order Workflow")
async def complete_order(order_data: dict) -> dict:
    """Main workflow with nested function calls."""
    
    # Step 1: Validate order
    validation = await validate_order(order_data)
    
    # Step 2: Process payment
    payment = await process_payment(order_data["id"], order_data["total"])
    
    # Step 3: Update inventory
    await update_inventory(order_data)
    
    return {
        "order_id": order_data["id"],
        "status": "completed",
        "validation": validation,
        "payment": payment
    }

# API endpoint
@app.post("/orders/complete")
async def complete_order_endpoint(order_request: OrderRequest):
    result = await complete_order(order_request.dict())
    return {"success": True, "result": result}
```

**Important Requirements:**

⚠️ **The general tracing decorator requires the unified middleware to work properly:**

1. **Middleware Setup**: Must use `unified_middleware` in your FastAPI application
2. **HTTP Requests**: Tracing only works via HTTP endpoints, not direct function calls
3. **Request Headers**: Include `X-Session-ID` and `X-User-Email` for better tracing context

**Benefits of General Tracing:**

- ✅ **Universal Compatibility**: Works with any Python function
- ✅ **Automatic Nesting**: Preserves parent-child relationships
- ✅ **Flexible Output Capture**: Supports both return values and captured results
- ✅ **Performance Monitoring**: Automatic timing and metadata collection
- ✅ **Error Tracking**: Comprehensive error information capture
- ✅ **Payload Optimization**: Configurable metadata filtering
- ✅ **Easy Integration**: Works alongside existing LLM, embedding, and vector DB tracers

## Custom Provider Registration

You can register custom providers using either approach:

### Using Direct Functions

```python
from observe_traces import register_provider, register_embedding_provider, register_reranking_provider

# Register custom LLM provider
register_provider(
    provider_name="my_custom_llm",
    token_parser=my_token_parser_function,
    response_extractor=my_response_extractor_function
)

# Register custom embedding provider
register_embedding_provider(
    provider_name="my_custom_embedding",
    token_parser=my_token_parser_function,
    price_calculator=my_price_calculator_function,
    embeddings_extractor=my_embeddings_extractor_function
)
```

### Using ObservabilityService

```python
from observe_traces import ObservabilityService

observability_service = ObservabilityService()

# Register custom providers
observability_service.register_llm_provider("my_custom_llm", my_custom_provider_instance)
observability_service.register_embedding_provider("my_custom_embedding", my_embedding_provider_instance)
observability_service.register_vectordb_provider("my_custom_vectordb", my_vectordb_provider_instance)
observability_service.register_reranking_provider("my_custom_reranking", my_reranking_provider_instance)
```

### Creating Custom Providers with Base Classes

For maximum customization, you can extend the base provider classes:

```python
from typing import Any, Dict, List
from observe_traces import ObservabilityService, LLMProvider, EmbeddingProvider

class MyCustomLLMProvider(LLMProvider):
    """Custom LLM provider implementation."""
    
    def __init__(self):
        super().__init__("my-custom-llm", self._extract_response)
    
    def parse_tokens(self, response_data: Dict[str, Any]) -> Dict[str, int]:
        """Parse tokens from your API response."""
        return {
            "prompt_tokens": response_data.get("input_tokens", 0),
            "completion_tokens": response_data.get("output_tokens", 0),
            "total_tokens": response_data.get("total_tokens", 0)
        }
    
    def calculate_cost(self, tokens_data: Dict[str, int], model_name: str) -> Dict[str, float]:
        """Calculate cost based on your pricing model."""
        input_cost = tokens_data.get("prompt_tokens", 0) * 0.00001  # Your pricing
        output_cost = tokens_data.get("completion_tokens", 0) * 0.00002
        return {
            "input": input_cost,
            "output": output_cost,
            "total": input_cost + output_cost
        }
    
    def _extract_response(self, data: Dict[str, Any]) -> str:
        """Extract response text from your API response."""
        return data.get("response", "")

class MyCustomEmbeddingProvider(EmbeddingProvider):
    """Custom embedding provider implementation."""
    
    def __init__(self):
        super().__init__("my-custom-embedding", self._extract_embeddings)
    
    def parse_tokens(self, response_data: Dict[str, Any]) -> Dict[str, int]:
        """Parse token usage from embedding response."""
        return {
            "total_tokens": response_data.get("usage", {}).get("tokens", 0)
        }
    
    def calculate_cost(self, tokens_data: Dict[str, int], model_name: str) -> Dict[str, float]:
        """Calculate embedding cost."""
        tokens = tokens_data.get("total_tokens", 0)
        cost = tokens * 0.0001  # Your embedding pricing
        return {"total": cost}
    
    def _extract_embeddings(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract embeddings from your API response."""
        return data.get("embeddings", [])

# Register custom providers
observability_service = ObservabilityService()
observability_service.register_llm_provider("my-custom-llm", MyCustomLLMProvider())
observability_service.register_embedding_provider("my-custom-embedding", MyCustomEmbeddingProvider())

# Use with decorators
@observability_service.llm_tracing("my-custom-llm")
async def my_custom_llm_function(model: str, prompt: str):
    # Your custom LLM API call
    return {"response": "Generated text", "input_tokens": 25, "output_tokens": 15}

@observability_service.embedding_tracing("my-custom-embedding")
async def my_custom_embedding_function(model: str, texts: List[str]):
    # Your custom embedding API call
    return {"embeddings": [{"values": [0.1, 0.2, 0.3]}], "usage": {"tokens": 10}}
```

## Features

- **Automatic Request Tracing**: Unique trace IDs for each request
- **Comprehensive Metadata**: Track user info, endpoints, and custom metadata
- **Cost Tracking**: Automatic calculation of token usage and costs
- **Performance Monitoring**: Response time measurements for all operations
- **Multi-Provider Support**: Works with various AI/ML providers
- **Flexible Integration**: Supports both tuple returns and single response objects
- **Context Management**: Maintains request state throughout the lifecycle
- **Token Cost Tracking**: Automatic calculation of costs based on provider-specific pricing
- **Streaming Support**: Comprehensive tracing for streaming LLM responses
- **Custom Provider Support**: Easy registration of new providers
- **API Call Tracing**: Create spans within existing traces to log API calls with input/output data
- **General Purpose Tracing**: Universal decorator for tracing any Python function with automatic nesting support

## Prerequisites

1. **Self-Hosted Langfuse**: You must have a Langfuse instance running. Configure:

   - `langfuse_host`: Your Langfuse server URL
   - `langfuse_public_key`: Your public API key
   - `langfuse_secret_key`: Your secret API key

2. **FastAPI Application**: The middleware is designed for FastAPI applications

## Best Practices

1. **Error Handling**: The decorators automatically handle exceptions while maintaining trace context
2. **Metadata**: Include relevant metadata in your middleware for better observability
3. **Resource Cleanup**: Call `LangfuseInitializer.close()` when shutting down your application
4. **Context Variables**: The system uses context variables to maintain request state
5. **Provider Registration**: Use the appropriate registration functions to add custom providers
6. **Token Cost Tracking**: Ensure your provider configurations include accurate pricing information
7. **Streaming Support**: Follow the specified format for streaming responses to ensure proper tracing

## Note

The tracing system uses context variables to maintain request state throughout the request lifecycle. It's essential to define your methods using the specified parameters for consistency and compatibility. The decorators handle both tuple returns (response data + raw response) and single raw response returns, making them flexible for different API implementations.

## Token Cost Validation

To ensure your application doesn't fail at runtime due to missing model pricing information, it's recommended to validate all your models during application startup. The `get_token_costs` utility function is used to retrieve pricing information for specific model/provider pairs.

Here's an example of how to validate all your models at application startup:

```python
from observe_traces import get_token_costs
from fastapi import FastAPI
import logging

app = FastAPI()

# Dictionary of all providers and models used in your application
USED_MODELS = {
    "openai": ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo", "text-embedding-ada-002"],
    "anthropic": ["claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"],
    "groq": ["llama-3-8b-8192", "mixtral-8x7b-32768"],
    "cohere": ["command", "command-light", "embed-english-v3.0"],
    "pinecone": ["rerank-v1"]
}

@app.on_event("startup")
async def validate_models():
    """Validate all models at application startup to fail fast if pricing info is missing"""
    missing_models = []

    for provider, models in USED_MODELS.items():
        for model in models:
            try:
                # This will raise ValueError if the model/provider pair is not found
                cost_info = get_token_costs(model, provider)
                logging.info(f"Validated model {model} for provider {provider}: {cost_info}")
            except ValueError as e:
                missing_models.append(f"{provider}/{model}")
                logging.error(f"Error validating model {model} for provider {provider}: {str(e)}")

    if missing_models:
        # Fail fast - if any model is missing, prevent application startup
        error_msg = f"Missing pricing information for models: {', '.join(missing_models)}"
        logging.critical(error_msg)
        raise RuntimeError(error_msg)

    logging.info("All models validated successfully")
```

This pattern ensures:

1. **Fail Fast:** Your application will fail at startup if any required model is missing pricing information, rather than failing during a user request
2. **Complete Coverage:** All provider/model combinations are validated in one place
3. **Better Error Messages:** Clear error messages identify which models are missing
4. **Runtime Safety:** No unexpected errors during request processing due to missing model information

For models not included in the default pricing configuration, you can extend the configuration or handle exceptions appropriately in your implementation.