"""Circuit breaker implementation for provider fault tolerance.

Implements the circuit breaker pattern to prevent cascading failures when a
provider is experiencing issues. The circuit breaker has three states:

- CLOSED: Normal operation, requests pass through
- OPEN: Provider is failing, requests fail fast without calling provider
- HALF_OPEN: Testing if provider has recovered

Configuration:
- fail_max: Number of failures before opening circuit (default: 5)
- timeout_duration: Seconds to wait before attempting recovery (default: 30)
- expected_exception: Exception types that trigger circuit breaker

Example:
    >>> breaker = ProviderCircuitBreaker(name="cerebras", fail_max=5)
    >>> result = await breaker.call_async(provider_call, request)
"""

# type: ignore

from __future__ import annotations

import asyncio
from collections.abc import Awaitable
from typing import Any, Callable, TypeVar

try:
    from pybreaker import CircuitBreaker, CircuitBreakerError
except ImportError:
    # Fallback if pybreaker not installed
    CircuitBreaker = None  # type: ignore[misc,assignment]
    CircuitBreakerError = Exception  # type: ignore[misc,assignment]

from .._exceptions import ProviderError, RateLimitError, TimeoutError
from .._logging import logger

T = TypeVar("T")


class ProviderCircuitBreaker:
    """Circuit breaker for provider API calls with async support.

    Wraps pybreaker's CircuitBreaker with provider-specific configuration
    and logging.

    Args:
        name: Circuit breaker name (typically provider name)
        fail_max: Maximum consecutive failures before opening circuit (default: 5)
        timeout_duration: Seconds to wait before attempting recovery (default: 30)
        expected_exception: Exception type(s) that trigger the circuit breaker

    Attributes:
        state: Current state ("closed", "open", or "half_open")
        fail_counter: Number of consecutive failures
    """

    def __init__(
        self,
        name: str,
        fail_max: int = 5,
        timeout_duration: int = 30,
        expected_exception: type[Exception] | tuple[type[Exception], ...] = (
            ProviderError,
            RateLimitError,
            TimeoutError,
        ),
    ) -> None:
        self.name = name
        self._fail_max = fail_max
        self._timeout_duration = timeout_duration

        if CircuitBreaker is None:
            logger.warning(
                "pybreaker not installed, circuit breaker disabled",
                provider=name,
            )
            self._breaker = None
        else:
            # Create circuit breaker with basic configuration
            self._breaker = CircuitBreaker(
                fail_max=fail_max,
                reset_timeout=timeout_duration,
                name=f"circuit_breaker_{name}",
            )  # type: ignore[call-arg]
            logger.info(
                "circuit_breaker_initialized",
                provider=name,
                fail_max=fail_max,
                reset_timeout=timeout_duration,
            )

    async def call_async(self, func: Callable[..., Awaitable[T]], *args: Any, **kwargs: Any) -> T:
        """Execute async function with circuit breaker protection.

        Args:
            func: Async function to execute
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func

        Returns:
            Result from func

        Raises:
            CircuitBreakerError: If circuit is open (provider is down)
            Exception: Any exception raised by func
        """
        if self._breaker is None:
            # Circuit breaker disabled (pybreaker not installed)
            return await func(*args, **kwargs)

        try:
            # pybreaker doesn't natively support async, so we wrap it
            def _sync_wrapper() -> Any:
                # Create a new event loop for this thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(func(*args, **kwargs))
                finally:
                    loop.close()

            # Run in thread to avoid blocking
            assert self._breaker is not None  # For type checker
            result = await asyncio.to_thread(lambda: self._breaker.call(_sync_wrapper))  # type: ignore[union-attr]
            return result
        except Exception as exc:
            if type(exc).__name__ == "CircuitBreakerError":
                logger.error(
                    "circuit_breaker_open",
                    provider=self.name,
                    error="Provider circuit breaker is open (failing fast)",
                )
                # Convert to our exception type
                from .._exceptions import ProviderError

                raise ProviderError(
                    provider=self.name,
                    original_error=Exception(
                        f"Circuit breaker open for {self.name} "
                        f"(too many failures, will retry after {self._timeout_duration}s)"
                    ),
                ) from exc
            raise

    @property
    def state(self) -> str:
        """Current circuit breaker state: 'closed', 'open', or 'half_open'."""
        if self._breaker is None:
            return "disabled"
        return str(self._breaker.current_state)

    @property
    def fail_counter(self) -> int:
        """Number of consecutive failures."""
        if self._breaker is None:
            return 0
        return getattr(self._breaker, "fail_counter", 0)

    def reset(self) -> None:
        """Manually reset the circuit breaker to closed state."""
        if self._breaker is not None:
            # Reset by setting fail_counter to 0
            if hasattr(self._breaker, "_fail_counter"):
                self._breaker._fail_counter = 0  # type: ignore[attr-defined]
            logger.info("circuit_breaker_reset", provider=self.name)
