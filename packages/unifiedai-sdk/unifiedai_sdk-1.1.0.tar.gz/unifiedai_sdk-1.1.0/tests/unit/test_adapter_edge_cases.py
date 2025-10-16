"""Test adapter edge cases and error scenarios."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from unifiedai._exceptions import RateLimitError
from unifiedai.adapters.bedrock import BedrockAdapter
from unifiedai.adapters.cerebras import CerebrasAdapter
from unifiedai.models.request import ChatRequest, Message


@pytest.mark.asyncio
async def test_cerebras_adapter_reasoning_no_tags() -> None:
    """Test Cerebras adapter when no <think> tags present."""
    adapter = CerebrasAdapter(credentials={"api_key": "test-key"})

    # Test extraction with no tags
    raw = {
        "id": "test",
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "Just a normal response without thinking",
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 5, "completion_tokens": 10, "total_tokens": 15},
        "created": 1697123456,
        "model": "llama3.1-8b",
        "time_info": {"total_time": 0.5, "completion_time": 0.4},
    }

    reasoning, cleaned = adapter._extract_reasoning_and_answer(raw)

    assert reasoning is None
    assert cleaned == "Just a normal response without thinking"


@pytest.mark.asyncio
async def test_cerebras_adapter_empty_response() -> None:
    """Test Cerebras adapter with empty response."""
    adapter = CerebrasAdapter(credentials={"api_key": "test-key"})

    raw = {
        "id": "test",
        "choices": [{"message": {"role": "assistant", "content": ""}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": 5, "completion_tokens": 0, "total_tokens": 5},
        "created": 1697123456,
        "model": "llama3.1-8b",
    }

    reasoning, cleaned = adapter._extract_reasoning_and_answer(raw)

    assert reasoning is None
    assert cleaned == ""


@pytest.mark.asyncio
async def test_bedrock_adapter_rate_limit_error() -> None:
    """Test Bedrock adapter handles throttling errors."""
    adapter = BedrockAdapter(
        credentials={
            "aws_access_key_id": "test",
            "aws_secret_access_key": "test",
            "region_name": "us-east-1",
        }
    )

    mock_client = MagicMock()
    # Create throttling exception
    throttling_exception = type("ThrottlingException", (Exception,), {})
    mock_client.converse.side_effect = throttling_exception("Rate limit exceeded")
    adapter._bedrock_client = mock_client

    request = ChatRequest(
        provider="bedrock",
        model="qwen.qwen3-32b-v1:0",
        messages=[Message(role="user", content="Hello")],
    )

    with pytest.raises(RateLimitError):
        await adapter.invoke(request)


@pytest.mark.asyncio
async def test_bedrock_adapter_system_message_handling() -> None:
    """Test Bedrock adapter handles system messages."""
    adapter = BedrockAdapter()

    messages = [
        Message(role="system", content="You are a helpful assistant"),
        Message(role="user", content="Hello"),
    ]

    bedrock_messages = adapter._convert_messages_to_bedrock(messages)

    # System messages should be skipped in Bedrock format
    assert len(bedrock_messages) == 1
    assert bedrock_messages[0]["role"] == "user"


@pytest.mark.asyncio
async def test_cerebras_adapter_fallback_models() -> None:
    """Test Cerebras adapter returns fallback models when API fails."""
    adapter = CerebrasAdapter(credentials={"api_key": "test-key"})

    # Force client creation to fail for list_models
    mock_client = MagicMock()
    mock_client.models.list.side_effect = Exception("API error")
    adapter._cb_client = mock_client

    models = await adapter.list_models()

    # Should return fallback models
    assert len(models) > 0
    assert any(m.id == "llama3.1-8b" for m in models)


@pytest.mark.asyncio
async def test_bedrock_adapter_fallback_models() -> None:
    """Test Bedrock adapter returns fallback models when API fails."""
    adapter = BedrockAdapter()

    # Force list_models to fail
    models = await adapter.list_models()

    # Should return fallback models
    assert len(models) > 0
    assert any("qwen" in m.id.lower() or "claude" in m.id.lower() for m in models)


@pytest.mark.asyncio
async def test_cerebras_adapter_no_time_info() -> None:
    """Test Cerebras adapter handles missing time_info."""
    from unittest.mock import AsyncMock

    adapter = CerebrasAdapter(credentials={"api_key": "test-key"})

    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.model_dump.return_value = {
        "id": "test",
        "choices": [
            {"message": {"role": "assistant", "content": "Hi"}, "finish_reason": "stop", "index": 0}
        ],
        "usage": {"prompt_tokens": 5, "completion_tokens": 10, "total_tokens": 15},
        "created": 1697123456,
        "model": "llama3.1-8b",
        # No time_info field
    }
    mock_client.chat.completions.create.return_value = mock_response
    adapter._cb_async_client = mock_client

    request = ChatRequest(
        provider="cerebras",
        model="llama3.1-8b",
        messages=[Message(role="user", content="Hello")],
    )

    response = await adapter.invoke(request)

    # Should still work with fallback metrics
    assert response is not None
    assert response.metrics is not None
    assert response.metrics.duration_ms is not None


@pytest.mark.asyncio
async def test_bedrock_adapter_stop_reason_mapping() -> None:
    """Test Bedrock adapter maps stop reasons correctly."""
    adapter = BedrockAdapter()

    # Test different stop reasons
    test_cases = [
        ("end_turn", "stop"),
        ("max_tokens", "length"),
        ("stop_sequence", "stop"),
        ("content_filtered", "content_filter"),
        ("unknown_reason", "unknown_reason"),  # Fallback
    ]

    for bedrock_reason, expected_openai_reason in test_cases:
        raw = {
            "output": {
                "message": {
                    "role": "assistant",
                    "content": [{"text": "Test"}],
                }
            },
            "stopReason": bedrock_reason,
            "usage": {"inputTokens": 5, "outputTokens": 10, "totalTokens": 15},
            "metrics": {"latencyMs": 300},
            "ResponseMetadata": {"RequestId": "test"},
        }

        response = adapter._normalize_response(
            raw=raw,
            fallback_id="test",
            created=1697123456,
            model="test-model",
        )

        assert response.choices[0].finish_reason == expected_openai_reason
