"""Test synchronous UnifiedAI client methods."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from unifiedai import UnifiedAI
from unifiedai.models.comparison import ComparisonResult
from unifiedai.models.model import Model, ModelList
from unifiedai.models.response import Choice, UnifiedChatResponse, Usage


def test_sync_client_create() -> None:
    """Test synchronous create method."""
    mock_response = UnifiedChatResponse(
        id="test-123",
        object="chat.completion",
        created=1697123456,
        model="llama3.1-8b",
        choices=[
            Choice(
                index=0,
                message={"role": "assistant", "content": "Hello!"},
                finish_reason="stop",
            )
        ],
        usage=Usage(prompt_tokens=5, completion_tokens=10, total_tokens=15),
    )

    # Mock adapter
    mock_adapter = MagicMock()
    mock_adapter.provider_name = "cerebras"
    mock_adapter.invoke_with_limit = MagicMock(return_value=mock_response)

    # Create a coroutine mock for async invoke

    async def mock_async_invoke(*args, **kwargs):  # type: ignore[no-untyped-def]
        return mock_response

    mock_adapter.invoke_with_limit = mock_async_invoke

    client = UnifiedAI()
    client._adapters["cerebras"] = mock_adapter

    response = client.chat.completions.create(
        provider="cerebras",
        model="llama3.1-8b",
        messages=[{"role": "user", "content": "Hello"}],
    )

    assert isinstance(response, UnifiedChatResponse)
    assert response.model == "llama3.1-8b"


def test_sync_client_compare() -> None:
    """Test synchronous compare method."""
    from datetime import datetime, timezone

    from unifiedai.models.comparison import ComparativeMetrics, ProviderResult
    from unifiedai.models.request import ChatRequest, Message

    mock_result = ComparisonResult(
        correlation_id="test-corr",
        timestamp=datetime.now(timezone.utc),
        request=ChatRequest(
            provider="comparison",
            model="llama3.1-8b",
            messages=[Message(role="user", content="Hello")],
            temperature=0.0,
            max_tokens=100,
        ),
        provider_a=ProviderResult(
            provider="cerebras",
            model="llama3.1-8b",
            success=True,
            response=UnifiedChatResponse(
                id="a",
                object="chat.completion",
                created=1697123456,
                model="llama3.1-8b",
                choices=[Choice(index=0, message={"role": "assistant", "content": "A"})],
                usage=Usage(),
            ),
        ),
        provider_b=ProviderResult(
            provider="bedrock",
            model="qwen.qwen3-32b-v1:0",
            success=True,
            response=UnifiedChatResponse(
                id="b",
                object="chat.completion",
                created=1697123456,
                model="qwen.qwen3-32b-v1:0",
                choices=[Choice(index=0, message={"role": "assistant", "content": "B"})],
                usage=Usage(),
            ),
        ),
        comparative_metrics=ComparativeMetrics(),
        winner="provider_a",
    )

    # Create async mock that returns the result
    async def mock_compare_async(*args, **kwargs):  # type: ignore[no-untyped-def]
        return mock_result

    # Patch the _compare_async function as imported in _client module
    with patch("unifiedai._client._compare_async", side_effect=mock_compare_async):
        client = UnifiedAI()
        result = client.chat.completions.compare(
            providers=["cerebras", "bedrock"],
            model="llama3.1-8b",
            messages=[{"role": "user", "content": "Hello"}],
        )

        assert isinstance(result, ComparisonResult)
        assert result.provider_a.success is True
        assert result.provider_b.success is True


def test_sync_client_models_list() -> None:
    """Test models.list() method."""
    mock_models = [
        Model(
            id="llama3.1-8b",
            object="model",
            created=1697123456,
            owned_by="meta",
        ),
        Model(
            id="llama3.1-70b",
            object="model",
            created=1697123456,
            owned_by="meta",
        ),
    ]

    # Mock adapter
    mock_adapter = MagicMock()
    mock_adapter.provider_name = "cerebras"

    # Create async mock for list_models

    async def mock_async_list_models(*args, **kwargs):  # type: ignore[no-untyped-def]
        return mock_models

    mock_adapter.list_models = mock_async_list_models

    client = UnifiedAI()
    client._adapters["cerebras"] = mock_adapter

    result = client.models.list(provider="cerebras")

    assert isinstance(result, ModelList)
    assert len(result.data) == 2
    assert result.data[0].id == "llama3.1-8b"


def test_sync_client_with_default_provider() -> None:
    """Test client with default provider."""
    client = UnifiedAI(provider="cerebras", model="llama3.1-8b")
    assert client.default_provider == "cerebras"
    assert client.default_model == "llama3.1-8b"


def test_sync_client_build_request() -> None:
    """Test _build_request helper."""
    from unifiedai.models.request import Message

    client = UnifiedAI()
    messages = [Message(role="user", content="Hello")]

    request = client._build_request(
        provider="cerebras",
        model="llama3.1-8b",
        messages=messages,
    )

    assert request.provider == "cerebras"
    assert request.model == "llama3.1-8b"
    assert len(request.messages) == 1


def test_sync_client_get_or_create_adapter() -> None:
    """Test adapter caching."""
    with patch("unifiedai._client.get_adapter") as mock_get_adapter:
        mock_adapter = MagicMock()
        mock_adapter.provider_name = "cerebras"
        mock_get_adapter.return_value = mock_adapter

        client = UnifiedAI()

        # First call should create adapter
        adapter1 = client._get_or_create_adapter("cerebras")
        assert adapter1 is not None

        # Second call should return cached adapter
        adapter2 = client._get_or_create_adapter("cerebras")
        assert adapter2 is adapter1

        # get_adapter should only be called once
        assert mock_get_adapter.call_count == 1


def test_sync_client_create_with_stream_raises_error() -> None:
    """Test that passing stream=True to create raises ValueError."""
    client = UnifiedAI()

    with pytest.raises(ValueError, match="Use chat.completions.stream"):
        client.chat.completions.create(
            provider="cerebras",
            model="llama3.1-8b",
            messages=[{"role": "user", "content": "Hello"}],
            stream=True,  # type: ignore
        )


def test_sync_client_create_with_providers_raises_error() -> None:
    """Test that passing providers to create raises TypeError."""
    client = UnifiedAI()

    with pytest.raises(TypeError, match="use compare_async for comparisons"):
        client.chat.completions.create(
            providers=["cerebras", "bedrock"],  # type: ignore
            model="llama3.1-8b",
            messages=[{"role": "user", "content": "Hello"}],
        )


def test_sync_client_create_without_provider_raises_error() -> None:
    """Test that create without provider or default raises ValueError."""
    client = UnifiedAI()  # No default provider

    with pytest.raises(ValueError, match="provider or providers must be specified"):
        client.chat.completions.create(
            model="llama3.1-8b",
            messages=[{"role": "user", "content": "Hello"}],
        )


@pytest.mark.asyncio
async def test_sync_client_create_async_deprecated() -> None:
    """Test that create_async shows deprecation warning."""
    mock_response = UnifiedChatResponse(
        id="test-123",
        object="chat.completion",
        created=1697123456,
        model="llama3.1-8b",
        choices=[
            Choice(
                index=0,
                message={"role": "assistant", "content": "Hello!"},
                finish_reason="stop",
            )
        ],
        usage=Usage(prompt_tokens=5, completion_tokens=10, total_tokens=15),
    )

    # Mock adapter
    mock_adapter = MagicMock()
    mock_adapter.provider_name = "cerebras"

    # Create async mock for invoke_with_limit
    async def mock_async_invoke(*args, **kwargs):  # type: ignore[no-untyped-def]
        return mock_response

    mock_adapter.invoke_with_limit = mock_async_invoke

    client = UnifiedAI(provider="cerebras")
    client._adapters["cerebras"] = mock_adapter

    # Test that it raises deprecation warning
    with pytest.warns(DeprecationWarning, match="create_async is deprecated"):
        result = await client.chat.completions.create_async(
            model="llama3.1-8b",
            messages=[{"role": "user", "content": "Hello"}],
        )

    assert isinstance(result, UnifiedChatResponse)


@pytest.mark.asyncio
async def test_sync_client_stream() -> None:
    """Test streaming method."""
    from unifiedai.models.stream import StreamChunk

    # Mock adapter with streaming
    mock_adapter = MagicMock()
    mock_adapter.provider_name = "cerebras"

    # Create async generator for stream_with_limit
    async def mock_stream_generator(*args, **kwargs):  # type: ignore[no-untyped-def]
        for i in range(3):
            yield StreamChunk(
                id="stream-test",
                model="llama3.1-8b",
                index=i,
                delta={"role": "assistant", "content": f"chunk{i}"},
            )

    mock_adapter.stream_with_limit = mock_stream_generator

    client = UnifiedAI(provider="cerebras")
    client._adapters["cerebras"] = mock_adapter

    # Collect chunks
    chunks = []
    async for chunk in client.chat.completions.stream(
        model="llama3.1-8b",
        messages=[{"role": "user", "content": "Hello"}],
    ):
        chunks.append(chunk)

    assert len(chunks) == 3
    assert chunks[0].delta["content"] == "chunk0"
    assert chunks[2].delta["content"] == "chunk2"


@pytest.mark.asyncio
async def test_sync_client_create_stream_alias() -> None:
    """Test create_stream is an alias for stream."""
    from unifiedai.models.stream import StreamChunk

    # Mock adapter
    mock_adapter = MagicMock()
    mock_adapter.provider_name = "cerebras"

    async def mock_stream_generator(*args, **kwargs):  # type: ignore[no-untyped-def]
        yield StreamChunk(
            id="stream-test",
            model="llama3.1-8b",
            index=0,
            delta={"role": "assistant", "content": "test"},
        )

    mock_adapter.stream_with_limit = mock_stream_generator

    client = UnifiedAI(provider="cerebras")
    client._adapters["cerebras"] = mock_adapter

    # Test the alias
    chunks = []
    async for chunk in client.chat.completions.create_stream(
        model="llama3.1-8b",
        messages=[{"role": "user", "content": "Hello"}],
    ):
        chunks.append(chunk)

    assert len(chunks) == 1
    assert chunks[0].delta["content"] == "test"


def test_sync_client_models_list_all_providers() -> None:
    """Test models.list() without provider (lists all)."""
    mock_models_cerebras = [
        Model(id="llama3.1-8b", object="model", created=1697123456, owned_by="meta"),
    ]
    mock_models_bedrock = [
        Model(id="claude-3-haiku", object="model", created=1697123456, owned_by="anthropic"),
    ]

    # Mock adapters
    mock_cerebras = MagicMock()
    mock_cerebras.provider_name = "cerebras"

    mock_bedrock = MagicMock()
    mock_bedrock.provider_name = "bedrock"

    # Create async mocks
    async def mock_list_cerebras(*args, **kwargs):  # type: ignore[no-untyped-def]
        return mock_models_cerebras

    async def mock_list_bedrock(*args, **kwargs):  # type: ignore[no-untyped-def]
        return mock_models_bedrock

    mock_cerebras.list_models = mock_list_cerebras
    mock_bedrock.list_models = mock_list_bedrock

    client = UnifiedAI()
    client._adapters["cerebras"] = mock_cerebras
    client._adapters["bedrock"] = mock_bedrock

    # List all models
    result = client.models.list()

    assert isinstance(result, ModelList)
    assert len(result.data) == 2
    assert any(m.id == "llama3.1-8b" for m in result.data)
    assert any(m.id == "claude-3-haiku" for m in result.data)


def test_sync_client_compare_with_models_dict() -> None:
    """Test compare with provider-specific model IDs."""
    from datetime import datetime, timezone

    from unifiedai.models.comparison import ComparativeMetrics, ProviderResult
    from unifiedai.models.request import ChatRequest, Message

    mock_result = ComparisonResult(
        correlation_id="test-corr",
        timestamp=datetime.now(timezone.utc),
        request=ChatRequest(
            provider="comparison",
            model="llama3.1-8b",
            messages=[Message(role="user", content="Hello")],
            temperature=0.0,
            max_tokens=100,
        ),
        provider_a=ProviderResult(
            provider="cerebras",
            model="llama3.1-8b",
            success=True,
            response=UnifiedChatResponse(
                id="a",
                object="chat.completion",
                created=1697123456,
                model="llama3.1-8b",
                choices=[Choice(index=0, message={"role": "assistant", "content": "A"})],
                usage=Usage(),
            ),
        ),
        provider_b=ProviderResult(
            provider="bedrock",
            model="meta.llama3-1-8b-instruct-v1:0",
            success=True,
            response=UnifiedChatResponse(
                id="b",
                object="chat.completion",
                created=1697123456,
                model="meta.llama3-1-8b-instruct-v1:0",
                choices=[Choice(index=0, message={"role": "assistant", "content": "B"})],
                usage=Usage(),
            ),
        ),
        comparative_metrics=ComparativeMetrics(),
        winner="provider_a",
    )

    # Create async mock that returns the result
    async def mock_compare_async(*args, **kwargs):  # type: ignore[no-untyped-def]
        return mock_result

    with patch("unifiedai._client._compare_async", side_effect=mock_compare_async):
        client = UnifiedAI()
        result = client.chat.completions.compare(
            providers=["cerebras", "bedrock"],
            models={
                "cerebras": "llama3.1-8b",
                "bedrock": "meta.llama3-1-8b-instruct-v1:0",
            },
            messages=[{"role": "user", "content": "Hello"}],
        )

        assert isinstance(result, ComparisonResult)
        assert result.provider_a.model == "llama3.1-8b"
        assert result.provider_b.model == "meta.llama3-1-8b-instruct-v1:0"
