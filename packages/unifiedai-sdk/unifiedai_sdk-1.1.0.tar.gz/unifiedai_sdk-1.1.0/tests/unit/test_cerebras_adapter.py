"""Test Cerebras adapter functionality."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from unifiedai._exceptions import AuthenticationError, InvalidRequestError, ProviderError
from unifiedai.adapters.cerebras import CerebrasAdapter
from unifiedai.models.request import ChatRequest, Message
from unifiedai.models.response import UnifiedChatResponse


@pytest.fixture
def cerebras_adapter() -> CerebrasAdapter:
    """Create a Cerebras adapter for testing."""
    return CerebrasAdapter(credentials={"api_key": "test-key"})


@pytest.mark.asyncio
async def test_cerebras_adapter_provider_name(cerebras_adapter: CerebrasAdapter) -> None:
    """Test provider_name property."""
    assert cerebras_adapter.provider_name == "cerebras"


@pytest.mark.asyncio
async def test_cerebras_adapter_invoke_success(
    cerebras_adapter: CerebrasAdapter, mock_cerebras_client: MagicMock
) -> None:
    """Test successful invocation."""
    cerebras_adapter._cb_async_client = mock_cerebras_client

    request = ChatRequest(
        provider="cerebras",
        model="llama3.1-8b",
        messages=[Message(role="user", content="Hello")],
    )

    response = await cerebras_adapter.invoke(request)

    assert isinstance(response, UnifiedChatResponse)
    assert response.model == "llama3.1-8b"
    assert response.choices[0].message["role"] == "assistant"
    assert response.metrics is not None
    assert response.provider_metadata is not None


@pytest.mark.asyncio
async def test_cerebras_adapter_authentication_error(
    cerebras_adapter: CerebrasAdapter,
) -> None:
    """Test authentication error handling."""
    from unittest.mock import AsyncMock

    mock_client = AsyncMock()
    mock_client.chat.completions.create.side_effect = Exception("API key invalid")
    cerebras_adapter._cb_async_client = mock_client

    request = ChatRequest(
        provider="cerebras",
        model="llama3.1-8b",
        messages=[Message(role="user", content="Hello")],
    )

    with pytest.raises(AuthenticationError) as exc_info:
        await cerebras_adapter.invoke(request)

    assert "cerebras" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_cerebras_adapter_invalid_request_error(
    cerebras_adapter: CerebrasAdapter,
) -> None:
    """Test invalid request error handling."""
    from unittest.mock import AsyncMock

    mock_client = AsyncMock()
    mock_client.chat.completions.create.side_effect = Exception("Invalid model")
    cerebras_adapter._cb_async_client = mock_client

    request = ChatRequest(
        provider="cerebras",
        model="invalid-model",
        messages=[Message(role="user", content="Hello")],
    )

    with pytest.raises(InvalidRequestError):
        await cerebras_adapter.invoke(request)


@pytest.mark.asyncio
async def test_cerebras_adapter_provider_error(
    cerebras_adapter: CerebrasAdapter,
) -> None:
    """Test generic provider error handling."""
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = Exception("Connection failed")
    cerebras_adapter._cb_client = mock_client

    request = ChatRequest(
        provider="cerebras",
        model="llama3.1-8b",
        messages=[Message(role="user", content="Hello")],
    )

    with pytest.raises(ProviderError):
        await cerebras_adapter.invoke(request)


@pytest.mark.asyncio
async def test_cerebras_adapter_reasoning_extraction(
    cerebras_adapter: CerebrasAdapter,
) -> None:
    """Test reasoning extraction from <think> tags."""
    from unittest.mock import AsyncMock

    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.model_dump.return_value = {
        "id": "test-123",
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "<think>Internal reasoning</think>Final answer",
                },
                "finish_reason": "stop",
                "index": 0,
            }
        ],
        "usage": {"prompt_tokens": 5, "completion_tokens": 10, "total_tokens": 15},
        "created": 1697123456,
        "model": "llama3.1-8b",
        "time_info": {
            "total_time": 0.5,
            "completion_time": 0.4,
            "prompt_time": 0.05,
            "queue_time": 0.05,
        },
    }
    mock_client.chat.completions.create.return_value = mock_response
    cerebras_adapter._cb_async_client = mock_client

    request = ChatRequest(
        provider="cerebras",
        model="llama3.1-8b",
        messages=[Message(role="user", content="Hello")],
    )

    response = await cerebras_adapter.invoke(request)

    # Content should have reasoning removed
    assert response.choices[0].message["content"] == "Final answer"
    # Reasoning should be in provider_metadata
    assert response.provider_metadata is not None
    assert response.provider_metadata.raw is not None
    assert "reasoning" in response.provider_metadata.raw


@pytest.mark.asyncio
async def test_cerebras_adapter_health_check_success(
    cerebras_adapter: CerebrasAdapter, mock_cerebras_client: MagicMock
) -> None:
    """Test health check returns healthy status."""
    cerebras_adapter._cb_client = mock_cerebras_client

    result = await cerebras_adapter.health_check()

    assert result["status"] == "healthy"
    assert result["provider"] == "cerebras"


@pytest.mark.asyncio
async def test_cerebras_adapter_health_check_failure(
    cerebras_adapter: CerebrasAdapter,
) -> None:
    """Test health check returns unhealthy status on error."""
    # Force client creation to fail
    with patch.object(cerebras_adapter, "_get_or_create_client", side_effect=Exception):
        result = await cerebras_adapter.health_check()

    assert result["status"] == "unhealthy"
    assert result["provider"] == "cerebras"


@pytest.mark.asyncio
async def test_cerebras_adapter_list_models(cerebras_adapter: CerebrasAdapter) -> None:
    """Test list_models returns available models."""
    mock_client = MagicMock()
    mock_model = MagicMock()
    mock_model.model_dump.return_value = {
        "id": "llama3.1-8b",
        "object": "model",
        "created": 1697123456,
        "owned_by": "meta",
    }
    mock_response = MagicMock()
    mock_response.data = [mock_model]
    mock_client.models.list.return_value = mock_response
    cerebras_adapter._cb_client = mock_client

    models = await cerebras_adapter.list_models()

    assert len(models) > 0
    assert all(hasattr(m, "id") for m in models)
