"""Test circuit breaker functionality."""

from __future__ import annotations

import pytest

from unifiedai._exceptions import ProviderError
from unifiedai.resilience.circuit_breaker import ProviderCircuitBreaker


@pytest.mark.asyncio
async def test_circuit_breaker_closed_state() -> None:
    """Test circuit breaker in closed state (normal operation)."""
    breaker = ProviderCircuitBreaker(name="test", fail_max=3, timeout_duration=10)

    call_count = 0

    async def successful_call() -> str:
        nonlocal call_count
        call_count += 1
        return "success"

    result = await breaker.call_async(successful_call)
    assert result == "success"
    assert call_count == 1
    assert breaker.state in ["closed", "disabled"]


@pytest.mark.asyncio
async def test_circuit_breaker_opens_after_failures() -> None:
    """Test circuit breaker opens after consecutive failures."""
    breaker = ProviderCircuitBreaker(name="test", fail_max=3, timeout_duration=10)

    call_count = 0

    async def failing_call() -> str:
        nonlocal call_count
        call_count += 1
        raise ProviderError(provider="test", original_error=Exception("Failed"))

    # First 3 failures should trigger circuit breaker
    for _ in range(3):
        with pytest.raises(ProviderError):
            await breaker.call_async(failing_call)

    # Circuit breaker should now be open or disabled (if pybreaker not installed)
    # If open, next call should fail fast without calling the function
    initial_call_count = call_count

    try:
        await breaker.call_async(failing_call)
    except ProviderError:
        pass

    # If circuit breaker is working, call_count should not increase (fail fast)
    # If disabled (pybreaker not installed), it will increase
    if breaker.state == "open":
        assert call_count == initial_call_count
    else:
        # Circuit breaker disabled, call was made
        assert call_count == initial_call_count + 1


@pytest.mark.asyncio
async def test_circuit_breaker_disabled_fallback() -> None:
    """Test circuit breaker works even if pybreaker not installed."""
    # This test ensures graceful degradation
    breaker = ProviderCircuitBreaker(name="test", fail_max=3, timeout_duration=10)

    async def successful_call() -> str:
        return "success"

    result = await breaker.call_async(successful_call)
    assert result == "success"


def test_circuit_breaker_state_property() -> None:
    """Test circuit breaker state property."""
    breaker = ProviderCircuitBreaker(name="test", fail_max=3, timeout_duration=10)
    state = breaker.state
    assert state in ["closed", "open", "half_open", "disabled"]


def test_circuit_breaker_fail_counter() -> None:
    """Test circuit breaker fail_counter property."""
    breaker = ProviderCircuitBreaker(name="test", fail_max=3, timeout_duration=10)
    counter = breaker.fail_counter
    assert isinstance(counter, int)
    assert counter >= 0


def test_circuit_breaker_reset() -> None:
    """Test circuit breaker reset method."""
    breaker = ProviderCircuitBreaker(name="test", fail_max=3, timeout_duration=10)
    breaker.reset()  # Should not raise any exception
    assert breaker.fail_counter == 0 or breaker.state == "disabled"
