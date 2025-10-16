"""Retry utilities (tenacity) for transient provider failures."""

from __future__ import annotations

from collections.abc import Awaitable
from typing import Any, Callable, TypeVar

from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from ._exceptions import RateLimitError, TimeoutError

T = TypeVar("T")


def with_retry(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
    """Decorator applying retry policy to an async function.

    Returns a function with the same signature as ``func`` that retries on
    ``RateLimitError`` and ``TimeoutError`` up to 3 times with exponential backoff.
    """

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((RateLimitError, TimeoutError)),
        reraise=True,
    )
    async def wrapped(*args: Any, **kwargs: Any) -> T:
        return await func(*args, **kwargs)

    return wrapped
