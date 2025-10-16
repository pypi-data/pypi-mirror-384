"""Asynchronous Unified AI client following OpenAI's Async client pattern.

Users construct ``AsyncUnifiedAI`` and await the same methods available on the
sync client, e.g., ``await client.chat.completions.create(...)``.

This client does not expose ``create_async``; the methods themselves are async.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from functools import cached_property
from typing import Any

from ._context import RequestContext
from ._logging import logger
from .adapters.base import BaseAdapter
from .adapters.registry import get_adapter
from .models.comparison import ComparisonResult
from .models.config import TimeoutConfig
from .models.request import Message
from .models.response import UnifiedChatResponse
from .models.stream import StreamChunk


class _AsyncCompletions:
    """OpenAI-style Chat Completions interface (asynchronous)."""

    def __init__(self, client: AsyncUnifiedAI) -> None:
        self._client = client

    async def create(
        self,
        *,
        provider: str | None = None,
        providers: list[str] | None = None,
        model: str | None = None,
        messages: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> UnifiedChatResponse:
        """Create a chat completion asynchronously.

        Args:
            provider: Provider name. Defaults to client's default provider.
            providers: Not supported here (use comparison API instead).
            model: Model identifier. Defaults to client's default model.
            messages: List of message dicts with ``role`` and ``content``.
            **kwargs: Reserved for future parameters; ignored.

        Returns:
            UnifiedChatResponse: Normalized OpenAI-style response.
        """
        if providers:
            raise TypeError(
                "AsyncUnifiedAI only supports solo create; use comparison API for compare"
            )
        adapter = self._client._get_or_create_adapter(
            provider or self._client.default_provider or ""
        )
        req_messages = [Message(role=m["role"], content=m["content"]) for m in (messages or [])]
        ctx = RequestContext.new()
        logger.info(
            "provider_invocation",
            correlation_id=ctx.correlation_id,
            provider=adapter.provider_name,
            model=model or self._client.default_model or "",
        )
        unified = await adapter.invoke_with_limit(
            request=self._client._build_request(
                adapter.provider_name, model or (self._client.default_model or ""), req_messages
            )
        )
        return unified

    async def stream(
        self,
        *,
        provider: str | None = None,
        model: str | None = None,
        messages: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[StreamChunk]:
        """Stream a chat completion as incremental chunks (async).

        Yields:
            StreamChunk: Incremental delta representing streamed content.
        """
        adapter = self._client._get_or_create_adapter(
            provider or self._client.default_provider or ""
        )
        req_messages = [Message(role=m["role"], content=m["content"]) for m in (messages or [])]
        async for chunk in adapter.stream_with_limit(
            request=self._client._build_request(
                adapter.provider_name, model or (self._client.default_model or ""), req_messages
            )
        ):
            yield chunk

    async def compare(
        self,
        *,
        providers: list[str],
        model: str | None = None,
        models: dict[str, str] | None = None,
        messages: list[dict[str, Any]],
        timeouts: TimeoutConfig | None = None,
    ) -> ComparisonResult:
        """Compare two providers side-by-side using identical inputs.

        Args:
            providers: Exactly two provider identifiers (e.g., ["cerebras", "bedrock"]).
            model: Model identifier shared across both providers. Mutually exclusive with
                ``models``.
            models: Dict mapping provider names to their specific model IDs. Mutually
                exclusive with ``model``. Example: ``{"cerebras": "llama3.1-8b", "bedrock":
                "meta.llama3-1-8b-instruct-v1:0"}``
            messages: Conversation messages (list of dicts with role/content).
            timeouts: Optional timeout configuration.

        Returns:
            ComparisonResult: Per-provider outcomes and comparative metrics.

        Examples:
            Shared model:
            >>> from unifiedai import AsyncUnifiedAI
            >>> async with AsyncUnifiedAI() as client:  # doctest: +SKIP
            ...     result = await client.chat.completions.compare(
            ...         providers=["cerebras", "bedrock"],
            ...         model="llama3.1-8b",
            ...         messages=[{"role": "user", "content": "Hello"}]
            ...     )

            Per-provider models:
            >>> async with AsyncUnifiedAI() as client:  # doctest: +SKIP
            ...     result = await client.chat.completions.compare(
            ...         providers=["cerebras", "bedrock"],
            ...         models={
            ...             "cerebras": "llama3.1-8b",
            ...             "bedrock": "meta.llama3-1-8b-instruct-v1:0"
            ...         },
            ...         messages=[{"role": "user", "content": "Hello"}]
            ...     )
        """
        from .core.comparison import compare_async as _compare_async

        return await _compare_async(
            providers=providers,
            model=model,
            models=models,
            messages=messages,
            timeouts=timeouts,
            credentials_by_provider=self._client._credentials_by_provider,
        )


class _AsyncChatAPI:
    """Async chat API container (lazy-loaded)."""

    def __init__(self, client: AsyncUnifiedAI) -> None:
        self.completions = _AsyncCompletions(client)


class AsyncUnifiedAI:
    """Asynchronous Unified AI client.

    Mirrors the synchronous client but methods are designed to be awaited
    without providing ``*_async`` variants.

    Resources are lazily loaded using @cached_property for efficiency:
    - ``chat``: Loaded on first access to ``client.chat``

    This approach:
    - Reduces memory usage by not initializing unused resources
    - Speeds up client construction
    - Matches OpenAI SDK pattern

    Args:
        provider: Optional default provider name.
        model: Optional default model identifier.
        credentials: Direct credential dictionary (e.g., {"api_key": "..."})
        credentials_by_provider: Per-provider credentials (e.g., {"cerebras": {...}})

    Example:
        >>> client = AsyncUnifiedAI(provider="cerebras")
        >>> # chat resource is not yet initialized
        >>> response = await client.chat.completions.create(...)  # ← loaded here
    """

    def __init__(
        self,
        provider: str | None = None,
        model: str | None = None,
        *,
        credentials: dict[str, str] | None = None,
        credentials_by_provider: dict[str, dict[str, str]] | None = None,
    ) -> None:
        self.default_provider = provider
        self.default_model = model
        # Resources (chat) are now lazy-loaded via @cached_property
        self._adapters: dict[str, BaseAdapter] = {}
        self._credentials = credentials or {}
        self._credentials_by_provider = credentials_by_provider or {}

    @cached_property
    def chat(self) -> _AsyncChatAPI:
        """Lazy-loaded async chat completions API.

        The chat resource is initialized only when first accessed, reducing
        memory usage and construction time for clients that don't use chat.

        Returns:
            _AsyncChatAPI: Async chat completions interface with ``completions`` sub-resource

        Example:
            >>> client = AsyncUnifiedAI(provider="cerebras")
            >>> # chat is not initialized yet
            >>> response = await client.chat.completions.create(...)  # ← initialized here
        """
        return _AsyncChatAPI(self)

    def _get_or_create_adapter(self, provider: str) -> BaseAdapter:
        """Return a cached adapter or create one for the given provider."""
        if provider not in self._adapters:
            effective_creds = (
                self._credentials_by_provider.get(provider) or self._credentials or None
            )
            self._adapters[provider] = get_adapter(provider, credentials=effective_creds)
        return self._adapters[provider]

    def _build_request(self, provider: str, model: str, messages: list[Message]):  # type: ignore[no-untyped-def]
        """Build a validated ChatRequest for adapter consumption."""
        from .models.request import ChatRequest

        return ChatRequest(
            provider=provider,
            model=model,
            messages=messages,
            temperature=0.7,
            max_tokens=256,
        )

    async def __aenter__(self) -> AsyncUnifiedAI:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: Any | None,
    ) -> None:
        await self.close()

    async def close(self) -> None:
        # Close all adapter resources (HTTP clients) concurrently
        import asyncio as _asyncio

        await _asyncio.gather(
            *[adapter.close() for adapter in self._adapters.values()], return_exceptions=True
        )
