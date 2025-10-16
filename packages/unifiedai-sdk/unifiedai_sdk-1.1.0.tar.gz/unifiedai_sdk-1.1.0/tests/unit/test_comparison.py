"""Test comparison mode functionality."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from unifiedai.core.comparison import (
    compare_async,
    normalize_role,
    preprocess_messages,
)
from unifiedai.models.comparison import ComparisonResult
from unifiedai.models.response import Choice, UnifiedChatResponse, Usage


@pytest.mark.asyncio
async def test_compare_async_success() -> None:
    """Test successful comparison of two providers."""
    messages = [{"role": "user", "content": "Hello"}]

    # Mock adapter responses
    mock_response_a = UnifiedChatResponse(
        id="test-a",
        object="chat.completion",
        created=1697123456,
        model="llama3.1-8b",
        choices=[Choice(index=0, message={"role": "assistant", "content": "Response A"})],
        usage=Usage(prompt_tokens=5, completion_tokens=10, total_tokens=15),
    )

    mock_response_b = UnifiedChatResponse(
        id="test-b",
        object="chat.completion",
        created=1697123456,
        model="qwen.qwen3-32b-v1:0",
        choices=[Choice(index=0, message={"role": "assistant", "content": "Response B"})],
        usage=Usage(prompt_tokens=5, completion_tokens=12, total_tokens=17),
    )

    async def mock_invoke_a(*args, **kwargs):  # type: ignore[no-untyped-def]
        return mock_response_a

    async def mock_invoke_b(*args, **kwargs):  # type: ignore[no-untyped-def]
        return mock_response_b

    with patch("unifiedai.core.comparison.get_adapter") as mock_get_adapter:
        mock_adapter_a = AsyncMock()
        mock_adapter_a.invoke_with_limit = mock_invoke_a
        mock_adapter_b = AsyncMock()
        mock_adapter_b.invoke_with_limit = mock_invoke_b

        def get_adapter_side_effect(provider, credentials=None):  # type: ignore[no-untyped-def]
            return mock_adapter_a if provider == "cerebras" else mock_adapter_b

        mock_get_adapter.side_effect = get_adapter_side_effect

        result = await compare_async(
            providers=["cerebras", "bedrock"],
            models={
                "cerebras": "llama3.1-8b",
                "bedrock": "qwen.qwen3-32b-v1:0",
            },
            messages=messages,
        )

    assert isinstance(result, ComparisonResult)
    assert result.provider_a.success is True
    assert result.provider_b.success is True
    assert result.provider_a.provider == "cerebras"
    assert result.provider_b.provider == "bedrock"
    assert result.winner in ["provider_a", "provider_b", "tie"]


@pytest.mark.asyncio
async def test_compare_async_partial_failure() -> None:
    """Test comparison with one provider failing."""
    messages = [{"role": "user", "content": "Hello"}]

    mock_response = UnifiedChatResponse(
        id="test",
        object="chat.completion",
        created=1697123456,
        model="llama3.1-8b",
        choices=[Choice(index=0, message={"role": "assistant", "content": "Success"})],
        usage=Usage(),
    )

    async def mock_invoke_success(*args, **kwargs):  # type: ignore[no-untyped-def]
        return mock_response

    async def mock_invoke_failure(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise Exception("Provider failed")

    with patch("unifiedai.core.comparison.get_adapter") as mock_get_adapter:
        mock_adapter_a = AsyncMock()
        mock_adapter_a.invoke_with_limit = mock_invoke_success
        mock_adapter_b = AsyncMock()
        mock_adapter_b.invoke_with_limit = mock_invoke_failure

        def get_adapter_side_effect(provider, credentials=None):  # type: ignore[no-untyped-def]
            return mock_adapter_a if provider == "cerebras" else mock_adapter_b

        mock_get_adapter.side_effect = get_adapter_side_effect

        result = await compare_async(
            providers=["cerebras", "bedrock"],
            model="llama3.1-8b",
            messages=messages,
        )

    assert result.provider_a.success is True
    assert result.provider_b.success is False
    assert result.provider_b.error is not None
    assert "failed" in result.provider_b.error.lower()


@pytest.mark.asyncio
async def test_compare_async_invalid_provider_count() -> None:
    """Test comparison rejects invalid provider count."""
    messages = [{"role": "user", "content": "Hello"}]

    with pytest.raises(ValueError, match="Exactly two providers"):
        await compare_async(
            providers=["cerebras"],  # Only one provider
            model="llama3.1-8b",
            messages=messages,
        )


@pytest.mark.asyncio
async def test_compare_async_missing_model_parameter() -> None:
    """Test comparison rejects when both model and models are None."""
    messages = [{"role": "user", "content": "Hello"}]

    with pytest.raises(ValueError, match="Must specify either"):
        await compare_async(
            providers=["cerebras", "bedrock"],
            model=None,
            models=None,
            messages=messages,
        )


@pytest.mark.asyncio
async def test_compare_async_both_model_parameters() -> None:
    """Test comparison rejects when both model and models are provided."""
    messages = [{"role": "user", "content": "Hello"}]

    with pytest.raises(ValueError, match="Specify either"):
        await compare_async(
            providers=["cerebras", "bedrock"],
            model="llama3.1-8b",
            models={"cerebras": "llama3.1-8b"},
            messages=messages,
        )


def test_preprocess_messages() -> None:
    """Test message preprocessing."""
    messages = [
        {"role": "user", "content": "  Hello  "},
        {"role": "assistant", "content": "Hi"},
    ]

    processed = preprocess_messages(messages)

    assert len(processed) == 2
    assert processed[0]["content"] == "Hello"  # Trimmed
    assert processed[0]["role"] == "user"


def test_normalize_role() -> None:
    """Test role normalization."""
    assert normalize_role("user") == "user"
    assert normalize_role("USER") == "user"
    assert normalize_role("assistant") == "assistant"
    assert normalize_role("ASSISTANT") == "assistant"
    assert normalize_role("system") == "system"
    assert normalize_role("SYSTEM") == "system"
    assert normalize_role("random") == "user"  # Fallback
