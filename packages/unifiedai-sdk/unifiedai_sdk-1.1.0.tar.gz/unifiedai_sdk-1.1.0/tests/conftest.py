"""Pytest configuration and shared fixtures for all tests."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture
def mock_cerebras_response() -> dict[str, Any]:
    """Sample Cerebras API response."""
    return {
        "id": "chatcmpl-test-123",
        "object": "chat.completion",
        "created": 1697123456,
        "model": "llama3.1-8b",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "Hello! How can I help you today?",
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 15,
            "total_tokens": 25,
        },
        "time_info": {
            "completion_time": 0.5,
            "prompt_time": 0.001,
            "queue_time": 0.1,
            "total_time": 0.601,
        },
    }


@pytest.fixture
def mock_bedrock_response() -> dict[str, Any]:
    """Sample Bedrock Converse API response."""
    return {
        "output": {
            "message": {
                "role": "assistant",
                "content": [{"text": "Hello! How can I assist you?"}],
            }
        },
        "stopReason": "end_turn",
        "usage": {
            "inputTokens": 12,
            "outputTokens": 10,
            "totalTokens": 22,
        },
        "metrics": {
            "latencyMs": 450,
        },
        "ResponseMetadata": {
            "RequestId": "test-bedrock-123",
        },
    }


@pytest.fixture
def mock_chat_request() -> dict[str, Any]:
    """Sample chat request payload."""
    return {
        "provider": "cerebras",
        "model": "llama3.1-8b",
        "messages": [{"role": "user", "content": "Hello"}],
        "temperature": 0.7,
        "max_tokens": 256,
    }


@pytest.fixture
def mock_credentials() -> dict[str, dict[str, str]]:
    """Mock credentials for all providers."""
    return {
        "cerebras": {"api_key": "test-cerebras-key"},
        "bedrock": {
            "aws_access_key_id": "test-access-key",
            "aws_secret_access_key": "test-secret-key",
            "region_name": "us-east-1",
        },
    }


@pytest.fixture
def mock_env_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set environment variables for tests."""
    monkeypatch.setenv("CEREBRAS_API_KEY", "test-cerebras-key")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "test-aws-key")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "test-aws-secret")
    monkeypatch.setenv("AWS_REGION", "us-east-1")


@pytest.fixture
def mock_cerebras_client() -> AsyncMock:
    """Mock Cerebras SDK client."""
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.model_dump.return_value = {
        "id": "test-123",
        "choices": [
            {
                "message": {"role": "assistant", "content": "Test response"},
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
    return mock_client


@pytest.fixture
def mock_bedrock_client() -> MagicMock:
    """Mock Bedrock boto3 client."""
    mock_client = MagicMock()
    mock_client.converse.return_value = {
        "output": {
            "message": {
                "role": "assistant",
                "content": [{"text": "Test response"}],
            }
        },
        "stopReason": "end_turn",
        "usage": {"inputTokens": 5, "outputTokens": 10, "totalTokens": 15},
        "metrics": {"latencyMs": 300},
        "ResponseMetadata": {"RequestId": "test-req-123"},
    }
    return mock_client


@pytest.fixture
def cerebras_adapter() -> Any:
    """Create a Cerebras adapter for testing."""
    from unifiedai.adapters.cerebras import CerebrasAdapter

    return CerebrasAdapter(credentials={"api_key": "test-key"})
