"""Test UnifiedAI and AsyncUnifiedAI clients."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from unifiedai import AsyncUnifiedAI, UnifiedAI
from unifiedai.models.comparison import ComparisonResult
from unifiedai.models.response import Choice, UnifiedChatResponse, Usage


def test_unifiedai_client_initialization() -> None:
    """Test UnifiedAI client initialization."""
    client = UnifiedAI()
    assert client is not None
    assert client.chat is not None
    assert client.models is not None


def test_asyncunifiedai_client_initialization() -> None:
    """Test AsyncUnifiedAI client initialization."""
    client = AsyncUnifiedAI()
    assert client is not None
    assert client.chat is not None
    # AsyncUnifiedAI doesn't have models.list() yet
    assert client.chat.completions is not None


@pytest.mark.asyncio
async def test_async_client_context_manager() -> None:
    """Test AsyncUnifiedAI context manager."""
    async with AsyncUnifiedAI() as client:
        assert client is not None

    # Should have cleaned up
    # (close method should have been called)


def test_unifiedai_create_with_credentials() -> None:
    """Test UnifiedAI with custom credentials."""
    client = UnifiedAI(
        credentials_by_provider={
            "cerebras": {"api_key": "test-key"},
        }
    )
    assert client is not None


@pytest.mark.asyncio
async def test_asyncunifiedai_create() -> None:
    """Test AsyncUnifiedAI create method."""
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

    # Mock at the adapter level, not get_adapter
    mock_adapter = AsyncMock()
    mock_adapter.provider_name = "cerebras"
    mock_adapter.invoke_with_limit = AsyncMock(return_value=mock_response)

    client = AsyncUnifiedAI()
    client._adapters["cerebras"] = mock_adapter

    response = await client.chat.completions.create(
        provider="cerebras",
        model="llama3.1-8b",
        messages=[{"role": "user", "content": "Hello"}],
    )

    assert isinstance(response, UnifiedChatResponse)
    assert response.model == "llama3.1-8b"


@pytest.mark.asyncio
async def test_asyncunifiedai_compare() -> None:
    """Test AsyncUnifiedAI compare method."""
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

    with patch(
        "unifiedai.core.comparison.compare_async",
        return_value=mock_result,
    ):
        client = AsyncUnifiedAI()
        result = await client.chat.completions.compare(
            providers=["cerebras", "bedrock"],
            model="llama3.1-8b",
            messages=[{"role": "user", "content": "Hello"}],
        )

        assert isinstance(result, ComparisonResult)
        assert result.provider_a.success is True
        assert result.provider_b.success is True


@pytest.mark.asyncio
async def test_asyncunifiedai_stream() -> None:
    """Test AsyncUnifiedAI streaming method."""
    from unifiedai.models.stream import StreamChunk

    # Mock adapter with streaming
    mock_adapter = AsyncMock()
    mock_adapter.provider_name = "cerebras"

    async def mock_stream_generator(*args, **kwargs):  # type: ignore[no-untyped-def]
        for i in range(2):
            yield StreamChunk(
                id="stream-test",
                model="llama3.1-8b",
                index=i,
                delta={"role": "assistant", "content": f"chunk{i}"},
            )

    mock_adapter.stream_with_limit = mock_stream_generator

    client = AsyncUnifiedAI(provider="cerebras")
    client._adapters["cerebras"] = mock_adapter

    # Collect chunks
    chunks = []
    async for chunk in client.chat.completions.stream(
        model="llama3.1-8b",
        messages=[{"role": "user", "content": "Hello"}],
    ):
        chunks.append(chunk)

    assert len(chunks) == 2
    assert chunks[0].delta["content"] == "chunk0"


@pytest.mark.asyncio
async def test_asyncunifiedai_create_with_providers_raises_error() -> None:
    """Test that passing providers to create raises TypeError."""
    client = AsyncUnifiedAI()

    with pytest.raises(TypeError, match="use comparison API"):
        await client.chat.completions.create(
            providers=["cerebras", "bedrock"],  # type: ignore
            model="llama3.1-8b",
            messages=[{"role": "user", "content": "Hello"}],
        )


@pytest.mark.asyncio
async def test_asyncunifiedai_close() -> None:
    """Test AsyncUnifiedAI close method."""
    mock_adapter1 = AsyncMock()
    mock_adapter1.close = AsyncMock()

    mock_adapter2 = AsyncMock()
    mock_adapter2.close = AsyncMock()

    client = AsyncUnifiedAI()
    client._adapters = {
        "cerebras": mock_adapter1,
        "bedrock": mock_adapter2,
    }

    await client.close()

    # Both adapters should have close called
    mock_adapter1.close.assert_called_once()
    mock_adapter2.close.assert_called_once()


@pytest.mark.asyncio
async def test_unifiedclient_close() -> None:
    """Test UnifiedClient close method."""
    mock_adapter1 = AsyncMock()
    mock_adapter1.close = AsyncMock()

    mock_adapter2 = AsyncMock()
    mock_adapter2.close = AsyncMock()

    client = UnifiedAI()
    client._adapters = {
        "cerebras": mock_adapter1,
        "bedrock": mock_adapter2,
    }

    await client.close()

    # Both adapters should have close called
    mock_adapter1.close.assert_called_once()
    mock_adapter2.close.assert_called_once()


@pytest.mark.asyncio
async def test_unifiedclient_context_manager() -> None:
    """Test UnifiedClient context manager."""
    mock_adapter = AsyncMock()
    mock_adapter.close = AsyncMock()

    async with UnifiedAI(provider="cerebras") as client:
        client._adapters["cerebras"] = mock_adapter
        assert client is not None

    # Close should be called on exit
    mock_adapter.close.assert_called_once()
