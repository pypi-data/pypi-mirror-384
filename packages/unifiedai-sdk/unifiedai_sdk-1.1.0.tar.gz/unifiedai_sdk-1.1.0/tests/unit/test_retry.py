"""Test retry logic with tenacity."""

from __future__ import annotations

import pytest

from unifiedai._exceptions import RateLimitError, TimeoutError
from unifiedai._retry import with_retry


@pytest.mark.asyncio
async def test_retry_success_on_first_attempt() -> None:
    """Test successful call on first attempt (no retry needed)."""
    call_count = 0

    @with_retry
    async def successful_call() -> str:
        nonlocal call_count
        call_count += 1
        return "success"

    result = await successful_call()
    assert result == "success"
    assert call_count == 1


@pytest.mark.asyncio
async def test_retry_success_after_failures() -> None:
    """Test successful call after 2 failures."""
    call_count = 0

    @with_retry
    async def flaky_call() -> str:
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise TimeoutError(
                message="Timeout", request_id="test_123", provider="test", status_code=408
            )
        return "success"

    result = await flaky_call()
    assert result == "success"
    assert call_count == 3


@pytest.mark.asyncio
async def test_retry_max_attempts_exceeded() -> None:
    """Test retry gives up after max attempts (3)."""
    call_count = 0

    @with_retry
    async def always_fails() -> str:
        nonlocal call_count
        call_count += 1
        raise RateLimitError(provider="test", original_error=Exception("Rate limit"))

    with pytest.raises(RateLimitError):
        await always_fails()

    assert call_count == 3  # Should try 3 times


@pytest.mark.asyncio
async def test_retry_does_not_retry_on_non_retryable_error() -> None:
    """Test retry does not retry on non-retryable exceptions."""
    call_count = 0

    @with_retry
    async def non_retryable_error() -> str:
        nonlocal call_count
        call_count += 1
        raise ValueError("Not retryable")

    with pytest.raises(ValueError):
        await non_retryable_error()

    assert call_count == 1  # Should not retry


@pytest.mark.asyncio
async def test_retry_with_rate_limit_error() -> None:
    """Test retry works with RateLimitError."""
    call_count = 0

    @with_retry
    async def rate_limited_call() -> str:
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise RateLimitError(provider="test", original_error=Exception("429"), retry_after=1)
        return "success"

    result = await rate_limited_call()
    assert result == "success"
    assert call_count == 2
