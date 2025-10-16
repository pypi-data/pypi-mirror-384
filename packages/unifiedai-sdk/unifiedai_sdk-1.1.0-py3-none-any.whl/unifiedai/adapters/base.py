"""Adapter base class and concurrency/HTTP pooling utilities.

All provider adapters must inherit from :class:`BaseAdapter` and implement the
abstract methods. The base class provides:

- A shared, pooled ``httpx.AsyncClient`` for connection reuse and HTTP/2 support
- A semaphore to enforce per-adapter concurrency limits
- Circuit breaker for fault tolerance (prevents cascading failures)
- Automatic retry with exponential backoff for transient errors
- Timeout enforcement per request
- Convenience wrappers ``invoke_with_limit`` and ``stream_with_limit`` that
  apply the semaphore, retry, circuit breaker, and timeout around provider calls
"""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

import httpx

from .._logging import logger
from .._retry import with_retry
from ..models.config import TimeoutConfig
from ..models.model import Model
from ..models.request import ChatRequest
from ..models.response import UnifiedChatResponse
from ..models.stream import StreamChunk
from ..resilience.circuit_breaker import ProviderCircuitBreaker


class BaseAdapter(ABC):
    """Abstract base class for all provider adapters.

    Subclasses must implement ``provider_name``, ``invoke``, ``invoke_streaming``,
    and ``health_check``. Implementations are responsible for authentication,
    provider-specific request translation, error mapping into the SDK's
    exceptions, and response normalization to ``UnifiedChatResponse``.

    The base class provides built-in resilience features:
    - Circuit breaker: Prevents cascading failures by failing fast when provider is down
    - Automatic retry: Retries transient failures (timeouts, rate limits) with exponential backoff
    - Timeout enforcement: Enforces per-request timeout with graceful cancellation
    - Concurrency limiting: Semaphore-based rate limiting per adapter

    Args:
        max_concurrent: Maximum concurrent requests per adapter instance.
        timeout: Optional custom ``httpx.Timeout`` configuration.
        timeouts: Optional timeout configuration for request processing.
        enable_circuit_breaker: Whether to enable circuit breaker (default: True).
        circuit_breaker_config: Optional circuit breaker configuration
            (fail_max, timeout_duration).
    """

    def __init__(
        self,
        max_concurrent: int = 10,
        timeout: httpx.Timeout | None = None,
        timeouts: TimeoutConfig | None = None,
        enable_circuit_breaker: bool = True,
        circuit_breaker_config: dict[str, int] | None = None,
    ) -> None:
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._timeouts = timeouts or TimeoutConfig()  # type: ignore[call-arg]
        self._client = httpx.AsyncClient(
            limits=httpx.Limits(
                max_keepalive_connections=20, max_connections=100, keepalive_expiry=30.0
            ),
            timeout=timeout or httpx.Timeout(connect=5.0, read=30.0, write=10.0, pool=5.0),
            http2=True,
            verify=True,
        )

        # Store circuit breaker config for lazy initialization (after provider_name is available)
        self._enable_circuit_breaker = enable_circuit_breaker
        self._circuit_breaker_config = circuit_breaker_config or {}
        self._circuit_breaker: ProviderCircuitBreaker | None = None

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return provider identifier.

        Returns:
            str: Short provider key (e.g., "cerebras", "bedrock").
        """

    @abstractmethod
    async def invoke(self, request: ChatRequest) -> UnifiedChatResponse:
        """Execute provider-specific API call.

        Args:
            request: Validated chat request.

        Returns:
            UnifiedChatResponse: Normalized OpenAI-style response.
        """

    @abstractmethod
    def invoke_streaming(self, request: ChatRequest) -> AsyncIterator[StreamChunk]:
        """Stream responses from provider as :class:`StreamChunk`.

        Implementations should be async generators yielding incremental deltas.
        """

    @abstractmethod
    async def health_check(self) -> dict[str, str]:
        """Check provider availability.

        Returns:
            dict[str, str]: Minimal provider health payload.
        """

    @abstractmethod
    async def list_models(self) -> list[Model]:
        """List available models for this provider.

        Returns:
            list[Model]: List of model objects supported by this provider.
        """

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()

    async def invoke_with_limit(self, request: ChatRequest) -> UnifiedChatResponse:
        """Run ``invoke`` with all resilience features.

        Includes: concurrency limit, timeout, retry, circuit breaker.

        Args:
            request: Chat request to process.

        Returns:
            UnifiedChatResponse: Provider response.

        Raises:
            TimeoutError: If request exceeds provider timeout.
            ProviderError: If circuit breaker is open or provider fails.
            RateLimitError: If provider rate limit is hit (after retries).
        """
        async with self._semaphore:
            return await self._invoke_with_resilience(request)

    def _get_or_create_circuit_breaker(self) -> ProviderCircuitBreaker | None:
        """Lazy initialization of circuit breaker (needs provider_name)."""
        if not self._enable_circuit_breaker:
            return None

        if self._circuit_breaker is None:
            self._circuit_breaker = ProviderCircuitBreaker(
                name=self.provider_name,
                fail_max=self._circuit_breaker_config.get("fail_max", 5),
                timeout_duration=self._circuit_breaker_config.get("timeout_duration", 30),
            )
        return self._circuit_breaker

    async def _invoke_with_resilience(self, request: ChatRequest) -> UnifiedChatResponse:
        """Apply retry, circuit breaker, and timeout to invoke.

        This method orchestrates the resilience patterns:
        1. Circuit breaker (outermost): Fail fast if provider is down
        2. Retry (middle): Retry transient failures with exponential backoff
        3. Timeout (innermost): Enforce per-request timeout
        4. Invoke (core): Actual provider call
        """
        circuit_breaker = self._get_or_create_circuit_breaker()

        if circuit_breaker is not None:
            # Circuit breaker wraps everything
            return await circuit_breaker.call_async(self._invoke_with_retry_and_timeout, request)
        else:
            # No circuit breaker, just retry and timeout
            return await self._invoke_with_retry_and_timeout(request)

    @with_retry  # Applies retry decorator with exponential backoff
    async def _invoke_with_retry_and_timeout(self, request: ChatRequest) -> UnifiedChatResponse:
        """Apply timeout enforcement around invoke."""
        provider_timeout = self._timeouts.provider_timeout

        logger.debug(
            "invoking_provider_with_timeout",
            provider=self.provider_name,
            model=request.model,
            timeout=provider_timeout,
        )

        try:
            # Enforce timeout using asyncio.wait_for
            result = await asyncio.wait_for(self.invoke(request), timeout=provider_timeout)
            return result
        except asyncio.TimeoutError as exc:
            logger.error(
                "provider_timeout",
                provider=self.provider_name,
                model=request.model,
                timeout=provider_timeout,
            )
            from .._exceptions import TimeoutError as SDKTimeoutError

            raise SDKTimeoutError(
                provider=self.provider_name,
                timeout_seconds=provider_timeout,
            ) from exc

    async def stream_with_limit(self, request: ChatRequest) -> AsyncIterator[StreamChunk]:
        """Run ``invoke_streaming`` under the adapter's concurrency limit.

        Note: Streaming does not apply retry or circuit breaker (streams are typically one-shot).
        Timeout is enforced at the chunk level.
        """
        async with self._semaphore:
            async for chunk in self.invoke_streaming(request):
                yield chunk
