"""Test Bedrock adapter functionality."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from unifiedai._exceptions import AuthenticationError, InvalidRequestError
from unifiedai.adapters.bedrock import BedrockAdapter
from unifiedai.models.request import ChatRequest, Message
from unifiedai.models.response import UnifiedChatResponse


@pytest.fixture
def bedrock_adapter() -> BedrockAdapter:
    """Create a Bedrock adapter for testing."""
    return BedrockAdapter(
        credentials={
            "aws_access_key_id": "test-key",
            "aws_secret_access_key": "test-secret",
            "region_name": "us-east-1",
        }
    )


@pytest.mark.asyncio
async def test_bedrock_adapter_provider_name(bedrock_adapter: BedrockAdapter) -> None:
    """Test provider_name property."""
    assert bedrock_adapter.provider_name == "bedrock"


@pytest.mark.asyncio
async def test_bedrock_adapter_invoke_success(
    bedrock_adapter: BedrockAdapter, mock_bedrock_client: MagicMock
) -> None:
    """Test successful invocation."""
    bedrock_adapter._bedrock_client = mock_bedrock_client

    request = ChatRequest(
        provider="bedrock",
        model="qwen.qwen3-32b-v1:0",
        messages=[Message(role="user", content="Hello")],
    )

    response = await bedrock_adapter.invoke(request)

    assert isinstance(response, UnifiedChatResponse)
    assert response.choices[0].message["role"] == "assistant"
    assert response.metrics is not None
    assert response.provider_metadata is not None


@pytest.mark.asyncio
async def test_bedrock_adapter_authentication_error(
    bedrock_adapter: BedrockAdapter,
) -> None:
    """Test authentication error handling."""
    mock_client = MagicMock()
    mock_client.converse.side_effect = Exception("credentials invalid")
    bedrock_adapter._bedrock_client = mock_client

    request = ChatRequest(
        provider="bedrock",
        model="qwen.qwen3-32b-v1:0",
        messages=[Message(role="user", content="Hello")],
    )

    with pytest.raises(AuthenticationError):
        await bedrock_adapter.invoke(request)


@pytest.mark.asyncio
async def test_bedrock_adapter_invalid_request_error(
    bedrock_adapter: BedrockAdapter,
) -> None:
    """Test invalid request error handling."""
    mock_client = MagicMock()
    error = type("ValidationException", (Exception,), {})("Invalid model")
    mock_client.converse.side_effect = error
    bedrock_adapter._bedrock_client = mock_client

    request = ChatRequest(
        provider="bedrock",
        model="invalid-model",
        messages=[Message(role="user", content="Hello")],
    )

    with pytest.raises(InvalidRequestError):
        await bedrock_adapter.invoke(request)


@pytest.mark.asyncio
async def test_bedrock_adapter_health_check_success(
    bedrock_adapter: BedrockAdapter, mock_bedrock_client: MagicMock
) -> None:
    """Test health check returns healthy status."""
    bedrock_adapter._bedrock_client = mock_bedrock_client

    result = await bedrock_adapter.health_check()

    assert result["status"] == "healthy"
    assert result["provider"] == "bedrock"


@pytest.mark.asyncio
async def test_bedrock_adapter_health_check_failure(
    bedrock_adapter: BedrockAdapter,
) -> None:
    """Test health check returns unhealthy status on error."""
    with patch.object(bedrock_adapter, "_get_or_create_client", side_effect=Exception):
        result = await bedrock_adapter.health_check()

    assert result["status"] == "unhealthy"
    assert result["provider"] == "bedrock"


@pytest.mark.asyncio
async def test_bedrock_adapter_convert_messages() -> None:
    """Test message conversion to Bedrock format."""
    adapter = BedrockAdapter()
    messages = [
        Message(role="user", content="Hello"),
        Message(role="assistant", content="Hi"),
    ]

    bedrock_messages = adapter._convert_messages_to_bedrock(messages)

    assert len(bedrock_messages) == 2
    assert bedrock_messages[0]["role"] == "user"
    assert bedrock_messages[0]["content"][0]["text"] == "Hello"


@pytest.mark.asyncio
async def test_bedrock_adapter_list_models(bedrock_adapter: BedrockAdapter) -> None:
    """Test list_models returns available models."""
    # Use fallback models since we're not mocking the full boto3 API
    models = await bedrock_adapter.list_models()

    assert len(models) > 0
    assert all(hasattr(m, "id") for m in models)
