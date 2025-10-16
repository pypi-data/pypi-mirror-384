import json
from datetime import datetime
from unittest.mock import MagicMock, mock_open, patch

import pytest

from observe_traces.config.context_util import (
    request_context,
    request_metadata_context,
    tracer_context,
)
from observe_traces.config.langfuse_init import LangfuseInitializer
from observe_traces.config.langfuse_service import _LangfuseService
from observe_traces.tracer.embed_tracer import (
    calculate_pinecone_price,
    embedding_tracing,
)
from observe_traces.tracer.llm_tracer import (
    llm_tracing,
    parse_groq_tokens,
    parse_openai_tokens,
)
from observe_traces.tracer.rerank_tracer import (
    calculate_pinecone_rerank_price,
    reranking_tracing,
)
from observe_traces.tracer.vector_tracer import (
    calculate_pinecone_price as calculate_pinecone_vectordb_price,
)
from observe_traces.tracer.vector_tracer import vectordb_tracing
from observe_traces.utils.token_costs import get_token_costs

# Test data
TEST_PUBLIC_KEY = "pk-lf-ca85952c-d5cf-4d21-8fff-fa2942a0e33b"
TEST_SECRET_KEY = "sk-lf-d1b12ef9-077e-431d-b6ab-1b764f744217"
TEST_HOST = "http://localhost:3000"
TEST_RELEASE = "3.46.0"
TEST_ENVIRONMENT = "unit-testing"

# Mock pricing data
MOCK_PRICING_DATA = {
    "gpt-3.5-turbo": {
        "input_cost_per_token": 0.0000015,
        "output_cost_per_token": 0.000002,
    },
    "claude-3-7-sonnet-20250219": {
        "input_cost_per_token": 0.000003,
        "output_cost_per_token": 0.000015,
    },
    "llama-3.3-70b-versatile": {
        "input_cost_per_token": 0.0000007,
        "output_cost_per_token": 0.0000007,
    },
    "llama-text-embed-v2": {
        "input_cost_per_token": 0.00000016,
        "output_cost_per_token": 0.0,
    },
    "pinecone-rerank-v0": {
        "input_cost_per_token": 0.0001,
        "output_cost_per_token": 0.0,
    },
}


@pytest.fixture
def mock_langfuse_client():
    with patch("observe_traces.config.langfuse_service.Langfuse") as mock:
        client = MagicMock()
        mock.return_value = client
        yield client


@pytest.fixture
def setup_langfuse(mock_langfuse_client):
    LangfuseInitializer.initialize(
        TEST_PUBLIC_KEY,
        TEST_SECRET_KEY,
        TEST_HOST,
        TEST_RELEASE,
        TEST_ENVIRONMENT,
    )
    yield
    LangfuseInitializer.close()


@pytest.fixture
def mock_trace():
    trace = MagicMock()
    tracer_context.set(trace)
    yield trace
    tracer_context.set(None)


@pytest.fixture
def mock_request():
    request = MagicMock()
    request_context.set(request)
    yield request
    request_context.set(None)


@pytest.fixture
def mock_metadata():
    metadata = {"user": "test_user", "apiEndpoint": "test_endpoint"}
    request_metadata_context.set(metadata)
    yield metadata
    request_metadata_context.set({})


# LangfuseInitializer Tests
def test_langfuse_initializer_initialization(mock_langfuse_client):
    LangfuseInitializer.initialize(
        TEST_PUBLIC_KEY,
        TEST_SECRET_KEY,
        TEST_HOST,
        TEST_RELEASE,
        TEST_ENVIRONMENT,
    )
    instance = LangfuseInitializer.get_instance()
    assert instance is not None
    assert instance.langfuse_public_key == TEST_PUBLIC_KEY
    assert instance.langfuse_secret_key == TEST_SECRET_KEY
    assert instance.langfuse_host == TEST_HOST
    assert instance.release == TEST_RELEASE
    assert instance.environment == TEST_ENVIRONMENT
    LangfuseInitializer.close()


def test_langfuse_initializer_singleton(mock_langfuse_client):
    LangfuseInitializer.initialize(
        TEST_PUBLIC_KEY,
        TEST_SECRET_KEY,
        TEST_HOST,
        TEST_RELEASE,
        TEST_ENVIRONMENT,
    )
    instance1 = LangfuseInitializer.get_instance()
    instance2 = LangfuseInitializer.get_instance()
    assert instance1 is instance2
    LangfuseInitializer.close()


def test_langfuse_initializer_close(mock_langfuse_client):
    LangfuseInitializer.initialize(
        TEST_PUBLIC_KEY,
        TEST_SECRET_KEY,
        TEST_HOST,
        TEST_RELEASE,
        TEST_ENVIRONMENT,
    )
    instance = LangfuseInitializer.get_instance()
    assert instance is not None
    LangfuseInitializer.close()
    instance = LangfuseInitializer.get_instance()
    assert instance is None


# Token Costs Tests
def test_get_token_costs():
    with patch(
        "builtins.open", mock_open(read_data=json.dumps(MOCK_PRICING_DATA))
    ):
        # Test OpenAI model
        costs = get_token_costs("gpt-3.5-turbo", "openai")
        assert costs["input_cost_per_token"] == 0.0000015
        assert costs["output_cost_per_token"] == 0.000002

        # Test Anthropic model
        costs = get_token_costs("claude-3-7-sonnet-20250219", "anthropic")
        assert costs["input_cost_per_token"] == 0.000003
        assert costs["output_cost_per_token"] == 0.000015

        # Test Groq model
        costs = get_token_costs("llama-3.3-70b-versatile", "groq")
        assert costs["input_cost_per_token"] == 0.0000007
        assert costs["output_cost_per_token"] == 0.0000007

        # Test embedding model
        costs = get_token_costs("llama-text-embed-v2", "pinecone")
        assert costs["input_cost_per_token"] == 0.00000016
        assert costs["output_cost_per_token"] == 0.0

        # Test reranking model
        costs = get_token_costs("pinecone-rerank-v0", "pinecone")
        assert costs["input_cost_per_token"] == 0.0001
        assert costs["output_cost_per_token"] == 0.0


def test_get_token_costs_invalid_model():
    with patch(
        "builtins.open", mock_open(read_data=json.dumps(MOCK_PRICING_DATA))
    ):
        with pytest.raises(ValueError):
            get_token_costs("invalid-model", "openai")


def test_get_token_costs_invalid_provider():
    with patch(
        "builtins.open", mock_open(read_data=json.dumps(MOCK_PRICING_DATA))
    ):
        with pytest.raises(ValueError):
            get_token_costs("gpt-3.5-turbo", "invalid-provider")


# Price Calculation Tests
def test_calculate_openai_price():
    # Test calculating price for OpenAI model using token costs
    token_costs = get_token_costs("gpt-3.5-turbo", "openai")
    prompt_tokens = 1000
    completion_tokens = 500

    input_price = (prompt_tokens / 1000000) * token_costs[
        "input_cost_per_token"
    ]
    output_price = (completion_tokens / 1000000) * token_costs[
        "output_cost_per_token"
    ]
    total_price = input_price + output_price

    price = {"input": input_price, "output": output_price, "total": total_price}

    assert "input" in price
    assert "output" in price
    assert "total" in price
    assert price["input"] == 0.0015  # 1000 * 0.0000015
    assert price["output"] == 0.001  # 500 * 0.000002
    assert price["total"] == 0.0025  # 0.0015 + 0.001


def test_calculate_anthropic_price():
    # Test calculating price for Anthropic model using token costs
    token_costs = get_token_costs("claude-3-7-sonnet-20250219", "anthropic")
    prompt_tokens = 1000
    completion_tokens = 500

    input_price = (prompt_tokens / 1000000) * token_costs[
        "input_cost_per_token"
    ]
    output_price = (completion_tokens / 1000000) * token_costs[
        "output_cost_per_token"
    ]
    total_price = input_price + output_price

    price = {"input": input_price, "output": output_price, "total": total_price}

    assert "input" in price
    assert "output" in price
    assert "total" in price
    assert price["input"] == 0.003  # 1000 * 0.000003
    assert price["output"] == 0.0075  # 500 * 0.000015
    assert price["total"] == 0.0105  # 0.003 + 0.0075


def test_calculate_groq_price():
    # Test calculating price for Groq model using token costs
    token_costs = get_token_costs("llama-3.3-70b-versatile", "groq")
    prompt_tokens = 1000
    completion_tokens = 500

    input_price = (prompt_tokens / 1000000) * token_costs[
        "input_cost_per_token"
    ]
    output_price = (completion_tokens / 1000000) * token_costs[
        "output_cost_per_token"
    ]
    total_price = input_price + output_price

    price = {"input": input_price, "output": output_price, "total": total_price}

    assert "input" in price
    assert "output" in price
    assert "total" in price
    assert price["input"] == 0.0007  # 1000 * 0.0000007
    assert price["output"] == 0.00035  # 500 * 0.0000007
    assert price["total"] == 0.00105  # 0.0007 + 0.00035


def test_calculate_pinecone_embedding_price():
    price = calculate_pinecone_price("llama-text-embed-v2", 1000)
    assert "tokens" in price
    assert "price_per_1M" in price
    assert "total" in price
    assert price["tokens"] == 1000
    assert price["price_per_1M"] == 0.16
    assert price["total"] > 0


def test_calculate_pinecone_rerank_price():
    price = calculate_pinecone_rerank_price(
        "pinecone-rerank-v0", {"rerank_units": 1000}
    )
    assert "rerank_units" in price
    assert "price_per_1K" in price
    assert "total" in price
    assert price["rerank_units"] == 1000
    assert price["price_per_1K"] == 0.10
    assert price["total"] > 0


def test_calculate_pinecone_vectordb_price():
    price = calculate_pinecone_vectordb_price("read", 1000)
    assert "units" in price
    assert "price" in price
    assert price["units"] == 1000
    assert price["price"] > 0


# Token Parsing Tests
def test_parse_openai_tokens():
    response_data = {
        "usage": {
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "total_tokens": 150,
        }
    }
    tokens = parse_openai_tokens(response_data)
    assert tokens["prompt_tokens"] == 100
    assert tokens["completion_tokens"] == 50
    assert tokens["total_tokens"] == 150


def test_parse_groq_tokens():
    response_data = {
        "usage": {
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "total_tokens": 150,
        }
    }
    tokens = parse_groq_tokens(response_data)
    assert tokens["prompt_tokens"] == 100
    assert tokens["completion_tokens"] == 50
    assert tokens["total_tokens"] == 150


# LLM Tracing Tests
@pytest.mark.asyncio
async def test_llm_tracing(
    setup_langfuse, mock_trace, mock_request, mock_metadata
):
    @llm_tracing("openai")
    async def mock_llm_call(self, **params):
        return {
            "choices": [{"message": {"content": "test response"}}],
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "total_tokens": 150,
            },
        }

    class MockLLM:
        @llm_tracing("openai")
        async def call(self, **params):
            return await mock_llm_call(self, **params)

    llm = MockLLM()
    result = await llm.call(
        model="gpt-3.5-turbo",
        chat_messages=["test message"],
        system_prompt="test system prompt",
    )
    assert result["choices"][0]["message"]["content"] == "test response"


# Embedding Tracing Tests
@pytest.mark.asyncio
async def test_embedding_tracing(
    setup_langfuse, mock_trace, mock_request, mock_metadata
):
    @embedding_tracing("pinecone")
    async def mock_embed_call(*args, **kwargs):
        return {
            "data": [{"values": [0.1, 0.2, 0.3]}],
            "usage": {"total_tokens": 100},
        }

    result = await mock_embed_call(
        model_name="llama-text-embed-v2",
        inputs=["test text"],
    )
    assert len(result["data"]) == 1
    assert len(result["data"][0]["values"]) == 3


# Reranking Tracing Tests
@pytest.mark.asyncio
async def test_reranking_tracing(
    setup_langfuse, mock_trace, mock_request, mock_metadata
):
    @reranking_tracing("pinecone")
    async def mock_rerank_call(*args, **kwargs):
        return {
            "data": [{"index": 0, "score": 0.9}],
            "usage": {"rerank_units": 1},
        }

    result = await mock_rerank_call(
        model_name="pinecone-rerank-v0",
        query="test query",
        documents=["test document"],
        top_n=1,
    )
    assert len(result["data"]) == 1
    assert result["data"][0]["index"] == 0
    assert result["data"][0]["score"] == 0.9


# Vector DB Tracing Tests
@pytest.mark.asyncio
async def test_vectordb_tracing(
    setup_langfuse, mock_trace, mock_request, mock_metadata
):
    @vectordb_tracing("pinecone", "read")
    async def mock_vectordb_call(*args, **kwargs):
        return {
            "matches": [{"id": "1", "score": 0.9}],
            "usage": {"read_units": 1},
        }

    result = await mock_vectordb_call(
        query=[0.1, 0.2, 0.3],
        top_k=1,
    )
    assert len(result["matches"]) == 1
    assert result["matches"][0]["id"] == "1"
    assert result["matches"][0]["score"] == 0.9


# LangfuseService Tests
@pytest.mark.asyncio
async def test_create_generation_for_llm(setup_langfuse, mock_trace):
    generation_data = {
        "model_name": "gpt-3.5-turbo",
        "service_provider": "openai",
        "input": {
            "user": ["test message"],
            "system": "test system prompt",
        },
        "output": "test response",
        "usage": {
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "total_tokens": 150,
        },
        "cost_details": {
            "input": 0.1,
            "output": 0.2,
            "total": 0.3,
        },
        "start_time": datetime.now(),
        "end_time": datetime.now(),
    }
    generation_id = await _LangfuseService.create_generation_for_LLM(
        "test_trace_id", generation_data, "test_name"
    )
    assert generation_id is not None


@pytest.mark.asyncio
async def test_create_span_for_embedding(setup_langfuse, mock_trace):
    span_data = {
        "service_provider": "pinecone",
        "model_name": "llama-text-embed-v2",
        "input": ["test text"],
        "tokens": {"total_tokens": 100},
        "price": {"total": 0.1},
        "input_count": 1,
        "response_time": 0.1,
        "start_time": datetime.now(),
        "end_time": datetime.now(),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "embedding_dimensions": 3,
    }
    span_id = await _LangfuseService.create_span_for_embedding(
        "test_trace_id", span_data, "test_name"
    )
    assert span_id is not None


@pytest.mark.asyncio
async def test_create_span_for_reranking(setup_langfuse, mock_trace):
    span_data = {
        "service_provider": "pinecone",
        "model_name": "pinecone-rerank-v0",
        "tokens": {"rerank_units": 1},
        "price": {"total": 0.1},
        "query": "test query",
        "documents": ["test document"],
        "document_count": 1,
        "top_n": 1,
        "rerank_results": ["test document"],
        "response_time": 0.1,
        "start_time": datetime.now(),
        "end_time": datetime.now(),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    span_id = await _LangfuseService.create_span_for_reranking(
        "test_trace_id", span_data, "test_name"
    )
    assert span_id is not None


@pytest.mark.asyncio
async def test_create_span_for_vectordb(setup_langfuse, mock_trace):
    span_data = {
        "service_provider": "pinecone",
        "operation_type": "read",
        "response": [{"id": "1", "score": 0.9}],
        "operation_details": {"top_k": 1},
        "units": 1,
        "price": 0.1,
        "query": [0.1, 0.2, 0.3],
        "start_time": datetime.now(),
        "end_time": datetime.now(),
        "response_time": 0.1,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    span_id = await _LangfuseService.create_span_for_vectorDB(
        "test_trace_id", span_data, "test_name"
    )
    assert span_id is not None
