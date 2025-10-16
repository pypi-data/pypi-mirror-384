"""Test Pydantic models for requests, responses, and comparisons."""

from __future__ import annotations

from datetime import datetime

import pytest
from pydantic import ValidationError

from unifiedai.models.comparison import (
    ComparativeMetrics,
    ComparisonResult,
    ProviderResult,
)
from unifiedai.models.config import SDKConfig, TimeoutConfig
from unifiedai.models.model import Model, ModelList
from unifiedai.models.request import ChatRequest, Message
from unifiedai.models.response import (
    Choice,
    ResponseMetrics,
    UnifiedChatResponse,
    Usage,
)
from unifiedai.models.stream import StreamChunk


def test_message_valid() -> None:
    """Test Message model with valid data."""
    msg = Message(role="user", content="Hello")
    assert msg.role == "user"
    assert msg.content == "Hello"


def test_message_invalid_role() -> None:
    """Test Message model rejects invalid role."""
    with pytest.raises(ValidationError):
        Message(role="invalid", content="Hello")  # type: ignore[arg-type]


def test_chat_request_valid() -> None:
    """Test ChatRequest model with valid data."""
    request = ChatRequest(
        provider="cerebras",
        model="llama3.1-8b",
        messages=[Message(role="user", content="Hello")],
        temperature=0.7,
        max_tokens=256,
    )
    assert request.provider == "cerebras"
    assert request.model == "llama3.1-8b"
    assert len(request.messages) == 1
    assert request.temperature == 0.7


def test_chat_request_invalid_temperature() -> None:
    """Test ChatRequest rejects invalid temperature."""
    with pytest.raises(ValidationError):
        ChatRequest(
            provider="cerebras",
            model="llama3.1-8b",
            messages=[Message(role="user", content="Hello")],
            temperature=3.0,  # > 2.0, should fail
        )


def test_usage_model() -> None:
    """Test Usage model."""
    usage = Usage(prompt_tokens=10, completion_tokens=20, total_tokens=30)
    assert usage.prompt_tokens == 10
    assert usage.completion_tokens == 20
    assert usage.total_tokens == 30


def test_response_metrics() -> None:
    """Test ResponseMetrics model."""
    metrics = ResponseMetrics(
        duration_ms=1500.5,
        provider_time_info={
            "queue_time": 100.2,
            "prompt_time": 200.3,
            "completion_time": 1200.0,
        },
    )
    assert metrics.duration_ms == 1500.5
    assert metrics.provider_time_info is not None
    assert metrics.provider_time_info["queue_time"] == 100.2
    assert metrics.provider_time_info["prompt_time"] == 200.3


def test_unified_chat_response() -> None:
    """Test UnifiedChatResponse model."""
    response = UnifiedChatResponse(
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
    assert response.id == "test-123"
    assert response.model == "llama3.1-8b"
    assert len(response.choices) == 1
    assert response.choices[0].message["content"] == "Hello!"


def test_provider_result_success() -> None:
    """Test ProviderResult for successful call."""
    result = ProviderResult(
        provider="cerebras",
        model="llama3.1-8b",
        success=True,
        response=UnifiedChatResponse(
            id="test",
            object="chat.completion",
            created=1697123456,
            model="llama3.1-8b",
            choices=[Choice(index=0, message={"role": "assistant", "content": "Hi"})],
            usage=Usage(),
        ),
        error=None,
    )
    assert result.success is True
    assert result.response is not None
    assert result.error is None


def test_provider_result_failure() -> None:
    """Test ProviderResult for failed call."""
    result = ProviderResult(
        provider="bedrock",
        model="meta.llama3-1-8b-instruct-v1:0",
        success=False,
        response=None,
        error="ProviderError: Connection timeout",
    )
    assert result.success is False
    assert result.response is None
    assert "timeout" in result.error.lower()


def test_comparison_result() -> None:
    """Test ComparisonResult model."""
    from datetime import timezone

    result = ComparisonResult(
        correlation_id="test-corr-123",
        timestamp=datetime.now(timezone.utc),
        request=ChatRequest(
            provider="comparison",
            model="llama3.1-8b",
            messages=[Message(role="user", content="Test")],
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
        comparative_metrics=ComparativeMetrics(speed_difference_ms=50.0),
        winner="provider_a",
    )
    assert result.provider_a.success is True
    assert result.provider_b.success is True
    assert result.winner == "provider_a"


def test_timeout_config_defaults() -> None:
    """Test TimeoutConfig default values."""
    config = TimeoutConfig()
    assert config.connect_timeout == 5.0
    assert config.read_timeout == 30.0
    assert config.provider_timeout == 60.0
    assert config.sdk_timeout == 90.0
    assert config.comparison_timeout == 120.0


def test_sdk_config_load(mock_env_vars: None) -> None:
    """Test SDKConfig loading from environment."""
    config = SDKConfig.load()
    # Check that config loads (values may be empty if env vars not set in test env)
    assert config is not None
    assert hasattr(config, "cerebras_key")
    assert hasattr(config, "aws_access_key_id")


def test_model_model() -> None:
    """Test Model model."""
    model = Model(
        id="llama3.1-8b",
        object="model",
        created=1697123456,
        owned_by="meta",
    )
    assert model.id == "llama3.1-8b"
    assert model.object == "model"


def test_model_list() -> None:
    """Test ModelList model."""
    model_list = ModelList(
        object="list",
        data=[
            Model(id="model1", object="model", created=1697123456, owned_by="meta"),
            Model(id="model2", object="model", created=1697123456, owned_by="openai"),
        ],
    )
    assert model_list.object == "list"
    assert len(model_list.data) == 2


def test_stream_chunk() -> None:
    """Test StreamChunk model."""
    chunk = StreamChunk(
        id="test-stream",
        model="llama3.1-8b",
        index=0,
        delta={"role": "assistant", "content": "Hello"},
        finish_reason=None,
    )
    assert chunk.id == "test-stream"
    assert chunk.delta["content"] == "Hello"
    assert chunk.finish_reason is None
