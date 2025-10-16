"""Synchronous Unified AI client and chat completions interface.

This module exposes the synchronous public API surface for the SDK, mirroring the
OpenAI-style interface. Users construct a ``UnifiedAI`` client (alias of
``UnifiedClient``) and access chat completions via
``client.chat.completions.create(...)``. Streaming is available through
``client.chat.completions.stream(...)`` which yields incremental ``StreamChunk``
instances.

Design notes:
- The client manages adapter instances (one per provider) and reuses a pooled
  HTTP client per adapter for efficiency.
- Concurrency is enforced per adapter with a semaphore.
- Request validation and normalization is done using Pydantic models.

Examples:
    >>> from unifiedai import UnifiedAI
    >>> client = UnifiedAI(provider="cerebras", model="llama3")
    >>> resp = client.chat.completions.create(
    ...     messages=[{"role": "user", "content": "Hello"}]  # doctest: +SKIP
    ... )
    >>> print(resp.choices[0].message["content"])  # doctest: +SKIP
"""

from __future__ import annotations

import asyncio
import types
import warnings
from collections.abc import AsyncIterator
from functools import cached_property
from typing import Any

from ._context import RequestContext
from ._logging import logger
from .adapters.base import BaseAdapter
from .adapters.registry import get_adapter
from .core.comparison import compare_async as _compare_async
from .models.comparison import ComparisonResult
from .models.config import TimeoutConfig
from .models.model import Model, ModelList
from .models.request import ChatRequest, Message
from .models.response import UnifiedChatResponse
from .models.stream import StreamChunk


class _Completions:
    """OpenAI-style Chat Completions interface (synchronous).

    This is attached to ``UnifiedClient.chat.completions`` and provides
    non-streaming (``create``) and streaming (``stream``) methods.
    """

    def __init__(self, client: UnifiedClient) -> None:
        self._client = client

    def create(
        self,
        *,
        provider: str | None = None,
        providers: list[str] | None = None,
        model: str | None = None,
        messages: list[dict[str, Any]] | None = None,
        stream: bool = False,
        **kwargs: Any,
    ) -> UnifiedChatResponse:
        """Create a chat completion synchronously.

        Args:
            provider: Provider name (e.g., "cerebras", "bedrock"). If omitted,
                falls back to the client's default provider.
            providers: Not supported for sync ``create`` (comparison requires async
                orchestration). Passing this raises ``TypeError``.
            model: Model identifier. If omitted, falls back to the client's default
                model.
            messages: List of message dicts with ``role`` and ``content``.
            stream: Must be False. For streaming responses, call ``stream(...)``.
            **kwargs: Reserved for future parameters; ignored.

        Returns:
            UnifiedChatResponse: Normalized OpenAI-style response.

        Raises:
            ValueError: If neither a provider nor a client default provider is set.
            TypeError: If ``providers`` is supplied (comparison not supported here).
        """
        if stream:
            raise ValueError("Use chat.completions.stream(...) for streaming responses")
        if providers:
            raise TypeError("create returns UnifiedChatResponse; use compare_async for comparisons")
        if provider or self._client.default_provider:
            adapter = self._client._get_or_create_adapter(
                provider or self._client.default_provider or ""
            )
            ctx = RequestContext.new()
            logger.info(
                "provider_invocation",
                correlation_id=ctx.correlation_id,
                provider=adapter.provider_name,
                model=model or self._client.default_model or "",
            )
            req_messages = [Message(**m) for m in (messages or [])]
            loop = asyncio.new_event_loop()
            try:
                asyncio.set_event_loop(loop)
                result: UnifiedChatResponse = loop.run_until_complete(
                    adapter.invoke_with_limit(
                        request=self._client._build_request(
                            adapter.provider_name,
                            model or (self._client.default_model or ""),
                            req_messages,
                        )
                    )
                )
                return result
            finally:
                loop.close()
        raise ValueError("provider or providers must be specified")

    async def create_async(
        self,
        *,
        provider: str | None = None,
        providers: list[str] | None = None,
        model: str | None = None,
        messages: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> UnifiedChatResponse:
        warnings.warn(
            "UnifiedAI.chat.completions.create_async is deprecated. "
            "Use AsyncUnifiedAI.chat.completions.create instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        """Create a chat completion asynchronously (deprecated).

        Prefer using ``AsyncUnifiedAI.chat.completions.create``.

        See ``create`` for parameters and return type.
        """
        if providers:
            raise TypeError(
                "create_async returns UnifiedChatResponse; use compare_async for comparisons"
            )
        adapter = self._client._get_or_create_adapter(
            provider or self._client.default_provider or ""
        )
        req_messages = [Message(role=m["role"], content=m["content"]) for m in (messages or [])]
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
        """Stream a chat completion as incremental chunks.

        Args:
            provider: Provider name. Defaults to client's default provider.
            model: Model identifier. Defaults to client's default model.
            messages: List of message dicts with ``role`` and ``content``.
            **kwargs: Reserved for future parameters; ignored.

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

    async def create_stream(
        self,
        *,
        provider: str | None = None,
        model: str | None = None,
        messages: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[StreamChunk]:
        """Back-compat alias for ``stream``.

        Prefer using ``stream`` directly.
        """
        async for chunk in self.stream(provider=provider, model=model, messages=messages, **kwargs):
            yield chunk

    def compare(
        self,
        *,
        providers: list[str],
        model: str | None = None,
        models: dict[str, str] | None = None,
        messages: list[dict[str, Any]],
        timeouts: TimeoutConfig | None = None,
    ) -> ComparisonResult:
        """Compare two providers side-by-side (synchronous wrapper).

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

        Note:
            This runs an event loop internally. For async servers, prefer
            ``AsyncUnifiedAI.chat.completions.compare``.

        Examples:
            Shared model (both providers use same ID):
            >>> from unifiedai import UnifiedAI
            >>> client = UnifiedAI()
            >>> result = client.chat.completions.compare(  # doctest: +SKIP
            ...     providers=["cerebras", "bedrock"],
            ...     model="llama3.1-8b",
            ...     messages=[{"role": "user", "content": "Hello"}]
            ... )

            Per-provider models (different IDs):
            >>> result = client.chat.completions.compare(  # doctest: +SKIP
            ...     providers=["cerebras", "bedrock"],
            ...     models={
            ...         "cerebras": "llama3.1-8b",
            ...         "bedrock": "meta.llama3-1-8b-instruct-v1:0"
            ...     },
            ...     messages=[{"role": "user", "content": "Hello"}]
            ... )
        """
        loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(
                _compare_async(
                    providers=providers,
                    model=model,
                    models=models,
                    messages=messages,
                    timeouts=timeouts,
                    credentials_by_provider=self._client._credentials_by_provider,
                )
            )
        finally:
            loop.close()


class _Models:
    """OpenAI-style Models interface (synchronous).

    Provides methods to list available models from providers.
    """

    def __init__(self, client: UnifiedClient) -> None:
        self._client = client

    def list(
        self,
        *,
        provider: str | None = None,
    ) -> ModelList:
        """List available models from one or all providers.

        Args:
            provider: Optional provider name to filter models. If None, lists
                models from all configured providers.

        Returns:
            ModelList: Object containing a list of Model objects.

        Examples:
            >>> from unifiedai import UnifiedAI
            >>> client = UnifiedAI()
            >>> models = client.models.list(provider="cerebras")  # doctest: +SKIP
            >>> for model in models.data:  # doctest: +SKIP
            ...     print(model.id)  # doctest: +SKIP
        """
        loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop)
            if provider:
                # List models from specific provider
                adapter = self._client._get_or_create_adapter(provider)
                models = loop.run_until_complete(adapter.list_models())
            else:
                # List models from all adapters
                all_models: list[Model] = []
                for provider_name in self._client._adapters.keys():
                    adapter = self._client._adapters[provider_name]
                    provider_models = loop.run_until_complete(adapter.list_models())
                    all_models.extend(provider_models)
                models = all_models

            return ModelList(object="list", data=models)
        finally:
            loop.close()


class _ChatAPI:
    """Lightweight container for ``chat.completions`` namespace."""

    def __init__(self, client: UnifiedClient) -> None:
        self.completions = _Completions(client)


class UnifiedClient:
    """Synchronous Unified AI client.

    Manages provider adapter instances and exposes an OpenAI-compatible chat API.

    Resources are lazily loaded using @cached_property for efficiency:
    - ``chat``: Loaded on first access to ``client.chat``
    - ``models``: Loaded on first access to ``client.models``

    This approach:
    - Reduces memory usage by not initializing unused resources
    - Speeds up client construction
    - Matches OpenAI SDK pattern

    Args:
        provider: Optional default provider name.
        model: Optional default model identifier.
        credentials: Direct credential dictionary (e.g., {"api_key": "..."})
        credentials_by_provider: Per-provider credentials (e.g., {"cerebras": {...}})

    Examples:
        >>> from unifiedai import UnifiedAI
        >>> client = UnifiedAI(provider="cerebras", model="llama3")
        >>> # chat resource is not yet initialized
        >>> client.chat.completions.create(  # doctest: +SKIP
        ...     messages=[{"role": "user", "content": "Hi"}]
        ... )  # ← chat loaded here on first access
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
        # Resources (chat, models) are now lazy-loaded via @cached_property
        self._adapters: dict[str, BaseAdapter] = {}
        self.timeouts = TimeoutConfig(
            connect_timeout=5.0,
            read_timeout=30.0,
            provider_timeout=60.0,
            sdk_timeout=90.0,
            comparison_timeout=120.0,
        )
        # Credentials precedence: per-provider > global > env (SDKConfig)
        self._credentials = credentials or {}
        self._credentials_by_provider = credentials_by_provider or {}

    @cached_property
    def chat(self) -> _ChatAPI:
        """Lazy-loaded chat completions API.

        The chat resource is initialized only when first accessed, reducing
        memory usage and construction time for clients that don't use chat.

        Returns:
            _ChatAPI: Chat completions interface with ``completions`` sub-resource

        Example:
            >>> client = UnifiedAI(provider="cerebras")
            >>> # chat is not initialized yet
            >>> response = client.chat.completions.create(...)  # ← initialized here
        """
        return _ChatAPI(self)

    @cached_property
    def models(self) -> _Models:
        """Lazy-loaded models API.

        The models resource is initialized only when first accessed, reducing
        memory usage and construction time for clients that don't list models.

        Returns:
            _Models: Models interface with ``list()`` method

        Example:
            >>> client = UnifiedAI(provider="cerebras")
            >>> # models is not initialized yet
            >>> all_models = client.models.list()  # ← initialized here
        """
        return _Models(self)

    def _get_or_create_adapter(self, provider: str) -> BaseAdapter:
        """Return a cached adapter or create one for the given provider.

        Args:
            provider: Provider identifier string.

        Returns:
            BaseAdapter: Provider-specific adapter instance.
        """
        if provider not in self._adapters:
            effective_creds = (
                self._credentials_by_provider.get(provider) or self._credentials or None
            )
            self._adapters[provider] = get_adapter(provider, credentials=effective_creds)
        return self._adapters[provider]

    def _build_request(self, provider: str, model: str, messages: list[Message]):  # type: ignore[no-untyped-def]
        """Build a validated ChatRequest for adapter consumption.

        Args:
            provider: Provider identifier.
            model: Model identifier.
            messages: Validated list of ``Message`` instances.

        Returns:
            ChatRequest: Pydantic-validated request object.
        """
        return ChatRequest(
            provider=provider,
            model=model,
            messages=messages,
            temperature=0.7,
            max_tokens=256,
        )

    async def __aenter__(self) -> UnifiedClient:
        """Enter async context manager returning self."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: types.TracebackType | None,
    ) -> None:
        """Ensure all resources are cleaned up on context exit."""
        await self.close()

    async def close(self) -> None:
        """Close all adapter resources (HTTP clients) concurrently."""
        await asyncio.gather(
            *[adapter.close() for adapter in self._adapters.values()], return_exceptions=True
        )
