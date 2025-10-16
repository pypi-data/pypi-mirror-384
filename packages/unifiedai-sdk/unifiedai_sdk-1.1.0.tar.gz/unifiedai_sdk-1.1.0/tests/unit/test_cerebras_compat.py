"""Test Cerebras SDK compatibility layer."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from unifiedai import AsyncCerebras, Cerebras


class TestCerebrasCompatSync:
    """Test synchronous Cerebras compatibility client."""

    def test_cerebras_initialization(self) -> None:
        """Test Cerebras client initialization."""
        client = Cerebras(api_key="test-key")
        assert client._cerebras_credentials == {"cerebras_key": "test-key"}
        assert hasattr(client, "chat")
        assert hasattr(client, "models")

    def test_cerebras_chat_completions_create(self) -> None:
        """Test chat completion with Cerebras model."""
        with patch("unifiedai._cerebras_compat.get_adapter") as mock_get_adapter:
            # Setup mock adapter
            mock_adapter = MagicMock()
            mock_adapter.provider_name = "cerebras"
            mock_response = MagicMock()
            mock_response.model_dump.return_value = {
                "id": "test-123",
                "object": "chat.completion",
                "created": 1697123456,
                "model": "llama3.1-8b",
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": "Hello!"},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {"prompt_tokens": 5, "completion_tokens": 10, "total_tokens": 15},
            }
            mock_adapter.invoke_raw_sync.return_value = mock_response
            mock_get_adapter.return_value = mock_adapter

            client = Cerebras(api_key="test-key")
            response = client.chat.completions.create(
                model="llama3.1-8b",
                messages=[{"role": "user", "content": "Hello"}],
            )

            assert response.model_dump()["id"] == "test-123"

    def test_cerebras_models_list(self) -> None:
        """Test listing models."""
        with (
            patch("unifiedai._cerebras_compat.get_adapter") as mock_get_adapter,
            patch("unifiedai._cerebras_compat.asyncio.new_event_loop") as mock_event_loop,
        ):
            mock_adapter = AsyncMock()

            class MockModel:
                def __init__(self, model_id: str) -> None:
                    self.id = model_id

            class MockModelListResponse:
                def __init__(self) -> None:
                    self.data = [MockModel("llama3.1-8b"), MockModel("qwen-3-32b")]

            # Mock the async call
            mock_adapter.list_models_raw.return_value = MockModelListResponse()
            mock_get_adapter.return_value = mock_adapter

            # Mock event loop
            mock_loop = MagicMock()
            mock_loop.run_until_complete.return_value = MockModelListResponse()
            mock_event_loop.return_value = mock_loop

            client = Cerebras(api_key="test-key")
            response = client.models.list()

            assert hasattr(response, "data")
            assert len(response.data) == 2


class TestCerebrasCompatAsync:
    """Test asynchronous Cerebras compatibility client."""

    def test_async_cerebras_initialization(self) -> None:
        """Test AsyncCerebras client initialization."""
        client = AsyncCerebras(api_key="test-key")
        assert client._cerebras_credentials == {"cerebras_key": "test-key"}
        assert hasattr(client, "chat")
        assert hasattr(client, "models")

    @pytest.mark.asyncio
    async def test_async_cerebras_chat_completions_create(self) -> None:
        """Test async chat completion."""
        with patch("unifiedai._cerebras_compat.get_adapter") as mock_get_adapter:
            mock_adapter = AsyncMock()
            mock_adapter.provider_name = "cerebras"
            mock_response = MagicMock()
            mock_response.model_dump.return_value = {
                "id": "test-123",
                "object": "chat.completion",
                "created": 1697123456,
                "model": "llama3.1-8b",
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": "Hello!"},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {"prompt_tokens": 5, "completion_tokens": 10, "total_tokens": 15},
            }
            mock_adapter.invoke_raw.return_value = mock_response
            mock_get_adapter.return_value = mock_adapter

            client = AsyncCerebras(api_key="test-key")
            response = await client.chat.completions.create(
                model="llama3.1-8b",
                messages=[{"role": "user", "content": "Hello"}],
            )

            assert response.model_dump()["id"] == "test-123"

    @pytest.mark.asyncio
    async def test_async_cerebras_models_list(self) -> None:
        """Test async model listing."""
        with patch("unifiedai._cerebras_compat.get_adapter") as mock_get_adapter:
            mock_adapter = AsyncMock()

            class MockModel:
                def __init__(self, model_id: str) -> None:
                    self.id = model_id

            # Mock list_models to return a list of Model objects
            mock_models = [MockModel("llama3.1-8b")]
            mock_adapter.list_models.return_value = mock_models
            mock_get_adapter.return_value = mock_adapter

            client = AsyncCerebras(api_key="test-key")
            response = await client.models.list()

            # Response should be a list
            assert isinstance(response, list)
            assert len(response) == 1
