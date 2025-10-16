"""Test streaming functionality for adapters."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from unifiedai.adapters.bedrock import BedrockAdapter
from unifiedai.adapters.cerebras import CerebrasAdapter
from unifiedai.models.request import ChatRequest, Message
from unifiedai.models.stream import StreamChunk


@pytest.mark.asyncio
async def test_cerebras_adapter_streaming_fallback() -> None:
    """Test Cerebras adapter streaming falls back to non-streaming."""
    from unifiedai.models.response import Choice, UnifiedChatResponse, Usage

    mock_response = UnifiedChatResponse(
        id="test-123",
        object="chat.completion",
        created=1697123456,
        model="llama3.1-8b",
        choices=[
            Choice(
                index=0,
                message={"role": "assistant", "content": "Hello from Cerebras!"},
                finish_reason="stop",
            )
        ],
        usage=Usage(prompt_tokens=5, completion_tokens=10, total_tokens=15),
    )

    adapter = CerebrasAdapter(credentials={"api_key": "test-key"})

    # Mock the invoke method to return our response
    async def mock_invoke(request: ChatRequest) -> UnifiedChatResponse:
        return mock_response

    adapter.invoke = mock_invoke  # type: ignore[method-assign]

    # Mock client to fail streaming
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = Exception("Streaming not supported")
    adapter._cb_client = mock_client

    request = ChatRequest(
        provider="cerebras",
        model="llama3.1-8b",
        messages=[Message(role="user", content="Hello")],
    )

    # Collect chunks
    chunks: list[StreamChunk] = []
    async for chunk in adapter.invoke_streaming(request):
        chunks.append(chunk)

    # Should have at least one chunk (fallback to non-streaming)
    assert len(chunks) >= 1
    assert chunks[0].delta["content"] == "Hello from Cerebras!"


@pytest.mark.asyncio
async def test_bedrock_adapter_streaming_fallback() -> None:
    """Test Bedrock adapter streaming falls back to non-streaming."""
    from unifiedai.models.response import Choice, UnifiedChatResponse, Usage

    mock_response = UnifiedChatResponse(
        id="test-123",
        object="chat.completion",
        created=1697123456,
        model="qwen.qwen3-32b-v1:0",
        choices=[
            Choice(
                index=0,
                message={"role": "assistant", "content": "Hello from Bedrock!"},
                finish_reason="stop",
            )
        ],
        usage=Usage(prompt_tokens=5, completion_tokens=10, total_tokens=15),
    )

    adapter = BedrockAdapter(
        credentials={
            "aws_access_key_id": "test-key",
            "aws_secret_access_key": "test-secret",
            "region_name": "us-east-1",
        }
    )

    # Mock the invoke method
    async def mock_invoke(request: ChatRequest) -> UnifiedChatResponse:
        return mock_response

    adapter.invoke = mock_invoke  # type: ignore[method-assign]

    # Mock client to fail streaming
    mock_client = MagicMock()
    mock_client.converse_stream.side_effect = Exception("Streaming not supported")
    adapter._bedrock_client = mock_client

    request = ChatRequest(
        provider="bedrock",
        model="qwen.qwen3-32b-v1:0",
        messages=[Message(role="user", content="Hello")],
    )

    # Collect chunks
    chunks: list[StreamChunk] = []
    async for chunk in adapter.invoke_streaming(request):
        chunks.append(chunk)

    # Should have at least one chunk (fallback)
    assert len(chunks) >= 1
    assert chunks[0].delta["content"] == "Hello from Bedrock!"


@pytest.mark.asyncio
async def test_stream_chunk_model() -> None:
    """Test StreamChunk model."""
    chunk = StreamChunk(
        id="test-stream",
        model="llama3.1-8b",
        index=0,
        delta={"role": "assistant", "content": "Hello"},
    )
    assert chunk.id == "test-stream"
    assert chunk.delta["content"] == "Hello"
    assert chunk.finish_reason is None


@pytest.mark.asyncio
async def test_stream_chunk_with_finish_reason() -> None:
    """Test StreamChunk with finish_reason."""
    chunk = StreamChunk(
        id="test-stream",
        model="llama3.1-8b",
        index=5,
        delta={"role": "assistant", "content": ""},
        finish_reason="stop",
    )
    assert chunk.finish_reason == "stop"
    assert chunk.delta["content"] == ""


@pytest.mark.asyncio
async def test_base_adapter_stream_with_limit() -> None:
    """Test BaseAdapter stream_with_limit applies semaphore."""
    from unifiedai.adapters.base import BaseAdapter
    from unifiedai.models.response import UnifiedChatResponse

    class MockStreamAdapter(BaseAdapter):
        @property
        def provider_name(self) -> str:
            return "mock"

        async def invoke(self, request: ChatRequest) -> UnifiedChatResponse:
            raise NotImplementedError

        async def invoke_streaming(self, request: ChatRequest):  # type: ignore[no-untyped-def]
            for i in range(3):
                yield StreamChunk(
                    id="test",
                    model=request.model,
                    index=i,
                    delta={"role": "assistant", "content": f"chunk{i}"},
                )

        async def health_check(self) -> dict[str, str]:
            return {"status": "healthy", "provider": "mock"}

        async def list_models(self):  # type: ignore[no-untyped-def]
            return []

    adapter = MockStreamAdapter(max_concurrent=5)
    request = ChatRequest(
        provider="mock",
        model="test-model",
        messages=[Message(role="user", content="Hello")],
    )

    chunks = []
    async for chunk in adapter.stream_with_limit(request):
        chunks.append(chunk)

    assert len(chunks) == 3
    assert chunks[0].delta["content"] == "chunk0"
    assert chunks[2].delta["content"] == "chunk2"
