"""Test BaseAdapter resilience features."""

from __future__ import annotations

import pytest

from unifiedai._exceptions import TimeoutError as SDKTimeoutError
from unifiedai.adapters.base import BaseAdapter
from unifiedai.models.request import ChatRequest, Message
from unifiedai.models.response import Choice, UnifiedChatResponse, Usage


class MockAdapter(BaseAdapter):
    """Mock adapter for testing BaseAdapter functionality."""

    @property
    def provider_name(self) -> str:
        return "mock"

    async def invoke(self, request: ChatRequest) -> UnifiedChatResponse:
        return UnifiedChatResponse(
            id="test-123",
            object="chat.completion",
            created=1697123456,
            model=request.model,
            choices=[
                Choice(
                    index=0,
                    message={"role": "assistant", "content": "Mock response"},
                    finish_reason="stop",
                )
            ],
            usage=Usage(prompt_tokens=5, completion_tokens=10, total_tokens=15),
        )

    async def invoke_streaming(self, request: ChatRequest):  # type: ignore[no-untyped-def]
        """Mock streaming (not used in tests)."""
        yield

    async def health_check(self) -> dict[str, str]:
        return {"status": "healthy", "provider": "mock"}

    async def list_models(self):  # type: ignore[no-untyped-def]
        """Mock list models."""
        return []


@pytest.fixture
def mock_adapter() -> MockAdapter:
    """Create a mock adapter for testing."""
    return MockAdapter(max_concurrent=5)


@pytest.mark.asyncio
async def test_base_adapter_invoke_with_limit_success(mock_adapter: MockAdapter) -> None:
    """Test invoke_with_limit successful call."""
    request = ChatRequest(
        provider="mock",
        model="test-model",
        messages=[Message(role="user", content="Hello")],
    )

    response = await mock_adapter.invoke_with_limit(request)

    assert isinstance(response, UnifiedChatResponse)
    assert response.model == "test-model"


@pytest.mark.asyncio
async def test_base_adapter_timeout_enforcement(mock_adapter: MockAdapter) -> None:
    """Test timeout is enforced."""
    import asyncio

    # Override invoke to simulate slow response
    async def slow_invoke(request: ChatRequest) -> UnifiedChatResponse:
        await asyncio.sleep(2)  # Sleep longer than timeout
        return UnifiedChatResponse(
            id="test",
            object="chat.completion",
            created=1697123456,
            model=request.model,
            choices=[Choice(index=0, message={"role": "assistant", "content": "Late"})],
            usage=Usage(),
        )

    mock_adapter.invoke = slow_invoke  # type: ignore[method-assign]
    mock_adapter._timeouts.provider_timeout = 0.1  # Very short timeout

    request = ChatRequest(
        provider="mock",
        model="test-model",
        messages=[Message(role="user", content="Hello")],
    )

    with pytest.raises(SDKTimeoutError) as exc_info:
        await mock_adapter.invoke_with_limit(request)

    assert "timed out" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_base_adapter_concurrency_limit(mock_adapter: MockAdapter) -> None:
    """Test concurrency limiting with semaphore."""
    import asyncio

    call_count = 0
    max_concurrent = 0
    current_concurrent = 0

    async def tracked_invoke(request: ChatRequest) -> UnifiedChatResponse:
        nonlocal call_count, max_concurrent, current_concurrent
        call_count += 1
        current_concurrent += 1
        max_concurrent = max(max_concurrent, current_concurrent)
        await asyncio.sleep(0.01)  # Simulate work
        current_concurrent -= 1
        return UnifiedChatResponse(
            id="test",
            object="chat.completion",
            created=1697123456,
            model=request.model,
            choices=[Choice(index=0, message={"role": "assistant", "content": "OK"})],
            usage=Usage(),
        )

    # Disable circuit breaker for this test
    mock_adapter._enable_circuit_breaker = False
    mock_adapter.invoke = tracked_invoke  # type: ignore[method-assign]

    request = ChatRequest(
        provider="mock",
        model="test-model",
        messages=[Message(role="user", content="Hello")],
    )

    # Fire 10 concurrent requests
    tasks = [mock_adapter.invoke_with_limit(request) for _ in range(10)]
    await asyncio.gather(*tasks)

    assert call_count == 10
    assert max_concurrent <= 5  # Should respect semaphore limit


@pytest.mark.asyncio
async def test_base_adapter_circuit_breaker_initialization() -> None:
    """Test circuit breaker is initialized correctly."""
    adapter = MockAdapter(
        enable_circuit_breaker=True,
        circuit_breaker_config={"fail_max": 10, "timeout_duration": 60},
    )

    circuit_breaker = adapter._get_or_create_circuit_breaker()

    assert circuit_breaker is not None or adapter._enable_circuit_breaker is False
    # If enabled, check configuration
    if circuit_breaker:
        assert circuit_breaker.name == "mock"


@pytest.mark.asyncio
async def test_base_adapter_circuit_breaker_disabled() -> None:
    """Test adapter works with circuit breaker disabled."""
    adapter = MockAdapter(enable_circuit_breaker=False)

    request = ChatRequest(
        provider="mock",
        model="test-model",
        messages=[Message(role="user", content="Hello")],
    )

    response = await adapter.invoke_with_limit(request)
    assert isinstance(response, UnifiedChatResponse)


@pytest.mark.asyncio
async def test_base_adapter_close() -> None:
    """Test adapter cleanup on close."""
    adapter = MockAdapter()
    await adapter.close()
    # Should not raise any exceptions
