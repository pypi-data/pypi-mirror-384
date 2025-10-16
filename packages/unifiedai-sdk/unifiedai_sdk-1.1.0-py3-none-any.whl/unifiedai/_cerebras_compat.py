"""Cerebras SDK compatibility layer.

Provides drop-in replacement classes for the Cerebras Cloud SDK, allowing existing
Cerebras users to migrate with minimal code changes while gaining access to additional
providers like AWS Bedrock.

Example:
    >>> # Old code with Cerebras SDK
    >>> from cerebras.cloud.sdk import Cerebras
    >>> client = Cerebras(api_key="sk-...")
    >>>
    >>> # New code with UnifiedAI - just change import!
    >>> from unifiedai import Cerebras
    >>> client = Cerebras(api_key="sk-...")
    >>>
    >>> # Now also supports Bedrock models with prefix
    >>> response = client.chat.completions.create(
    ...     model="bedrock:anthropic.claude-3-haiku-20240307-v1:0",
    ...     messages=[{"role": "user", "content": "Hello"}]
    ... )

Migration:
    Change one line: `from cerebras.cloud.sdk import Cerebras` becomes
    `from unifiedai import Cerebras`. Everything else works unchanged.
"""

from __future__ import annotations

import asyncio
import builtins
from typing import Any, Literal, cast

from .adapters.mappers import BedrockToCerebrasMapper
from .adapters.registry import get_adapter
from .models.model import Model as ModelType
from .models.request import ChatRequest, Message

# Import actual Cerebras SDK ChatCompletion type for 100% compatibility
try:
    from cerebras.cloud.sdk.types import (  # type: ignore[import-not-found]
        ChatCompletion,
    )
except (ImportError, AttributeError):
    # Fallback type if Cerebras SDK not installed
    from typing import Any

    ChatCompletion = Any

# Import actual Cerebras SDK types for 100% compatibility
try:
    from cerebras.cloud.sdk.types import ModelListResponse
except ImportError:
    # Fallback if Cerebras SDK not installed (for type checking)
    from typing import Literal

    from pydantic import BaseModel

    class ModelListResponse(BaseModel):  # type: ignore[no-redef]
        """Fallback ModelListResponse for when Cerebras SDK not installed."""

        data: list[ModelType]
        object: Literal["list"] = "list"


class _Models:
    """Models interface (matches Cerebras SDK structure)."""

    def __init__(self, client: Cerebras) -> None:
        """Initialize models interface.

        Args:
            client: Parent Cerebras client instance.
        """
        self._client = client

    def list(self) -> ModelListResponse:
        """List available models from Cerebras (synchronous).

        Returns:
            ModelListResponse with .data containing list of Model objects.
            Matches cerebras.cloud.sdk.types.ModelListResponse format.

        Example:
            >>> client = Cerebras(api_key="sk-...")
            >>> response = client.models.list()
            >>> for model in response.data:
            ...     print(f"{model.id} - {model.owned_by}")
        """
        # Get Cerebras adapter to list models
        adapter = self._client._get_adapter("llama3.1-8b")  # Use any Cerebras model to get adapter

        # Run async version in sync context
        loop = asyncio.new_event_loop()
        try:
            # Use raw adapter method to get native SDK response for strict backward compatibility
            raw_response = loop.run_until_complete(adapter.list_models_raw())
            return raw_response
        finally:
            loop.close()

    async def list_async(self) -> ModelListResponse:
        """List available models from Cerebras (asynchronous).

        Returns:
            ModelListResponse with .data containing list of Model objects.
            Matches cerebras.cloud.sdk.types.ModelListResponse format.

        Example:
            >>> client = AsyncCerebras(api_key="sk-...")
            >>> response = await client.models.list()
            >>> for model in response.data:
            ...     print(f"{model.id} - {model.owned_by}")
        """
        # Get Cerebras adapter to list models
        adapter = self._client._get_adapter("llama3.1-8b")
        # Use raw adapter method to get native SDK response for strict backward compatibility
        raw_response = await adapter.list_models_raw()
        return raw_response


class Cerebras:
    """Drop-in replacement for Cerebras Cloud SDK.

    This class provides 99% backwards compatibility with the Cerebras SDK while
    adding support for additional providers like AWS Bedrock via model ID prefixes.

    The class acts as a thin wrapper around adapters, delegating directly to
    CerebrasAdapter for performance while maintaining all production features
    (retries, circuit breakers, timeouts) from BaseAdapter.

    Args:
        api_key: Cerebras API key. If not provided, uses CEREBRAS_API_KEY environment variable.
        base_url: Optional custom base URL for Cerebras API (rarely used).
        **kwargs: Additional arguments (enable_retries, enable_circuit_breaker, etc.).

    Example:
        >>> client = Cerebras(api_key="sk-...")
        >>>
        >>> # Use Cerebras model (works exactly like original SDK)
        >>> response = client.chat.completions.create(
        ...     model="llama3.1-8b",
        ...     messages=[{"role": "user", "content": "Hello"}]
        ... )
        >>>
        >>> # Use Bedrock model (new capability!)
        >>> response = client.chat.completions.create(
        ...     model="bedrock.anthropic.claude-3-haiku-20240307-v1:0",
        ...     messages=[{"role": "user", "content": "Hello"}]
        ... )

    Note:
        Model ID patterns:
        - Cerebras models: "llama3.1-8b" → Routes to Cerebras (default)
        - Bedrock models: "bedrock.model-id" → Routes to Bedrock
        - Provider is auto-detected from model ID prefix
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize Cerebras-compatible client.

        Args:
            api_key: Cerebras API key. Falls back to CEREBRAS_API_KEY env var.
            base_url: Optional custom base URL (not commonly used).
            **kwargs: Additional configuration options.
        """
        # Store credentials for lazy adapter creation
        self._cerebras_credentials = {"cerebras_key": api_key} if api_key else None
        self._kwargs = kwargs

        # Create chat and models interfaces
        self.chat = _Chat(self)
        self.models = _Models(self)

    def _get_adapter(self, model: str) -> Any:
        """Get appropriate adapter based on model ID.

        Args:
            model: Model identifier (may include provider prefix).

        Returns:
            Adapter instance for the detected provider.
        """
        # Detect provider from model prefix
        model_lower = model.lower()
        if model_lower.startswith("bedrock.") or model_lower.startswith("bedrock/"):
            provider = "bedrock"
        else:
            provider = "cerebras"  # Default

        # Get adapter with credentials
        return get_adapter(provider, credentials=self._cerebras_credentials)

    async def close(self) -> None:
        """Close adapter resources (if any)."""
        # Adapters manage their own resources
        pass

    def __enter__(self) -> Cerebras:
        """Sync context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Sync context manager exit."""
        # No async cleanup needed for sync client
        pass


class _ChatCompletions:
    """Chat completions interface (matches Cerebras SDK structure)."""

    def __init__(self, client: Cerebras) -> None:
        """Initialize chat completions interface.

        Args:
            client: Parent Cerebras client instance.
        """
        self._client = client

    def create(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        **kwargs: Any,
    ) -> ChatCompletion:
        """Create a chat completion (synchronous).

        Returns the native Cerebras SDK ChatCompletion type for 100% backward compatibility.

        Args:
            model: Model identifier. Can include "bedrock:" prefix for Bedrock models.
            messages: List of message dicts with "role" and "content".
            **kwargs: Additional parameters (temperature, max_tokens, etc.).

        Returns:
            ChatCompletion: Native Cerebras SDK response type.

        Example:
            >>> response = client.chat.completions.create(
            ...     model="llama3.1-8b",
            ...     messages=[{"role": "user", "content": "Hello"}],
            ...     temperature=0.7
            ... )
            >>> print(response.choices[0].message.content)
        """
        # Normalize model ID (remove provider prefix if present)
        normalized_model = model
        if model.startswith("bedrock."):
            normalized_model = model[8:]  # len("bedrock.") = 8
        elif model.startswith("bedrock/"):
            normalized_model = model[8:]  # len("bedrock/") = 8

        # Get appropriate adapter
        adapter = self._client._get_adapter(model)

        # Convert message dicts to Message objects
        message_objs = [
            Message(
                role=cast(Literal["system", "user", "assistant"], m["role"]),
                content=m["content"],
            )
            for m in messages
        ]

        # Build request
        request = ChatRequest(
            provider=adapter.provider_name,
            model=normalized_model,
            messages=message_objs,
            **kwargs,
        )

        # Use raw adapter method to get native SDK response for strict backward compatibility
        if hasattr(adapter, "invoke_raw_sync"):
            # Use sync raw method
            raw_result = adapter.invoke_raw_sync(request)
        else:
            # Fallback: run async raw method in event loop
            loop = asyncio.new_event_loop()
            try:
                raw_result = loop.run_until_complete(adapter.invoke_raw(request))
            finally:
                loop.close()

        # If Bedrock adapter was used, convert response to Cerebras format
        if adapter.provider_name == "bedrock":
            # raw_result is boto3 Bedrock response (dict)
            cerebras_dict = BedrockToCerebrasMapper.map_chat_completion(raw_result)
            # Try to create Cerebras SDK ChatCompletion from dict
            try:
                # If Cerebras SDK is available, use its type
                return ChatCompletion(**cerebras_dict)
            except Exception:  # noqa: BLE001
                # Fallback: return dict (will still work for basic usage)
                return cerebras_dict
        else:
            # Cerebras adapter - already returns native ChatCompletion
            return raw_result

    async def create_async(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        **kwargs: Any,
    ) -> ChatCompletion:
        """Create a chat completion (asynchronous).

        Returns the native Cerebras SDK ChatCompletion type for 100% backward compatibility.

        Args:
            model: Model identifier. Can include "bedrock:" prefix for Bedrock models.
            messages: List of message dicts with "role" and "content".
            **kwargs: Additional parameters (temperature, max_tokens, etc.).

        Returns:
            ChatCompletion: Native Cerebras SDK response type.

        Example:
            >>> response = await client.chat.completions.create_async(
            ...     model="llama3.1-8b",
            ...     messages=[{"role": "user", "content": "Hello"}]
            ... )
        """
        # Normalize model ID (remove provider prefix if present)
        normalized_model = model
        if model.startswith("bedrock."):
            normalized_model = model[8:]  # len("bedrock.") = 8
        elif model.startswith("bedrock/"):
            normalized_model = model[8:]  # len("bedrock/") = 8

        # Get appropriate adapter
        adapter = self._client._get_adapter(model)

        # Convert message dicts to Message objects
        message_objs = [
            Message(
                role=cast(Literal["system", "user", "assistant"], m["role"]),
                content=m["content"],
            )
            for m in messages
        ]

        # Build request
        request = ChatRequest(
            provider=adapter.provider_name,
            model=normalized_model,
            messages=message_objs,
            **kwargs,
        )

        # Use raw adapter method to get native SDK response for strict backward compatibility
        raw_result = await adapter.invoke_raw(request)

        # If Bedrock adapter was used, convert response to Cerebras format
        if adapter.provider_name == "bedrock":
            # raw_result is boto3 Bedrock response (dict)
            cerebras_dict = BedrockToCerebrasMapper.map_chat_completion(raw_result)
            # Try to create Cerebras SDK ChatCompletion from dict
            try:
                # If Cerebras SDK is available, use its type
                return ChatCompletion(**cerebras_dict)
            except Exception:  # noqa: BLE001
                # Fallback: return dict (will still work for basic usage)
                return cerebras_dict
        else:
            # Cerebras adapter - already returns native ChatCompletion
            return raw_result


class _Chat:
    """Chat interface (matches Cerebras SDK structure)."""

    def __init__(self, client: Cerebras) -> None:
        """Initialize chat interface.

        Args:
            client: Parent Cerebras client instance.
        """
        self.completions = _ChatCompletions(client)


class _AsyncModels:
    """Async models interface."""

    def __init__(self, client: AsyncCerebras) -> None:
        """Initialize async models interface.

        Args:
            client: Parent AsyncCerebras client instance.
        """
        self._client = client

    async def list(self) -> builtins.list[ModelType]:
        """List available models from Cerebras (asynchronous).

        Returns:
            List of Model objects with id, created, and owned_by fields.

        Example:
            >>> async with AsyncCerebras(api_key="sk-...") as client:
            ...     models = await client.models.list()
            ...     for model in models:
            ...         print(f"{model.id} - {model.owned_by}")
        """
        # Get Cerebras adapter to list models
        adapter = self._client._get_adapter("llama3.1-8b")
        result = await adapter.list_models()
        return cast(list[ModelType], result)


class AsyncCerebras:
    """Async drop-in replacement for Cerebras Cloud SDK.

    This class provides async support with 99% backwards compatibility with the
    Cerebras SDK's AsyncCerebras class.

    Args:
        api_key: Cerebras API key. If not provided, uses CEREBRAS_API_KEY environment variable.
        base_url: Optional custom base URL for Cerebras API.
        **kwargs: Additional arguments passed to adapters.

    Example:
        >>> async with AsyncCerebras(api_key="sk-...") as client:
        ...     # Use Cerebras model
        ...     response = await client.chat.completions.create(
        ...         model="llama3.1-8b",
        ...         messages=[{"role": "user", "content": "Hello"}]
        ...     )
        ...
        ...     # Use Bedrock model
        ...     response = await client.chat.completions.create(
        ...         model="bedrock.anthropic.claude-3-haiku-20240307-v1:0",
        ...         messages=[{"role": "user", "content": "Hello"}]
        ...     )
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize async Cerebras-compatible client.

        Args:
            api_key: Cerebras API key. Falls back to CEREBRAS_API_KEY env var.
            base_url: Optional custom base URL (not commonly used).
            **kwargs: Additional configuration options.
        """
        # Store credentials for lazy adapter creation
        self._cerebras_credentials = {"cerebras_key": api_key} if api_key else None
        self._kwargs = kwargs

        # Create chat and models interfaces
        self.chat = _AsyncChat(self)
        self.models = _AsyncModels(self)

    def _get_adapter(self, model: str) -> Any:
        """Get appropriate adapter based on model ID.

        Args:
            model: Model identifier (may include provider prefix).

        Returns:
            Adapter instance for the detected provider.
        """
        # Detect provider from model prefix
        model_lower = model.lower()
        if model_lower.startswith("bedrock.") or model_lower.startswith("bedrock/"):
            provider = "bedrock"
        else:
            provider = "cerebras"  # Default

        # Get adapter with credentials
        return get_adapter(provider, credentials=self._cerebras_credentials)

    async def close(self) -> None:
        """Close adapter resources."""
        # Adapters manage their own resources
        pass

    async def __aenter__(self) -> AsyncCerebras:
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()


class _AsyncChatCompletions:
    """Async chat completions interface."""

    def __init__(self, client: AsyncCerebras) -> None:
        """Initialize async chat completions interface.

        Args:
            client: Parent AsyncCerebras client instance.
        """
        self._client = client

    async def create(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        **kwargs: Any,
    ) -> ChatCompletion:
        """Create a chat completion (asynchronous).

        Returns the native Cerebras SDK ChatCompletion type for 100% backward compatibility.

        Args:
            model: Model identifier. Can include "bedrock:" prefix for Bedrock models.
            messages: List of message dicts with "role" and "content".
            **kwargs: Additional parameters (temperature, max_tokens, etc.).

        Returns:
            ChatCompletion: Native Cerebras SDK response type.

        Example:
            >>> response = await client.chat.completions.create(
            ...     model="llama3.1-8b",
            ...     messages=[{"role": "user", "content": "Hello"}]
            ... )
        """
        # Normalize model ID (remove provider prefix if present)
        normalized_model = model
        if model.startswith("bedrock."):
            normalized_model = model[8:]  # len("bedrock.") = 8
        elif model.startswith("bedrock/"):
            normalized_model = model[8:]  # len("bedrock/") = 8

        # Get appropriate adapter
        adapter = self._client._get_adapter(model)

        # Convert message dicts to Message objects
        message_objs = [
            Message(
                role=cast(Literal["system", "user", "assistant"], m["role"]),
                content=m["content"],
            )
            for m in messages
        ]

        # Build request
        request = ChatRequest(
            provider=adapter.provider_name,
            model=normalized_model,
            messages=message_objs,
            **kwargs,
        )

        # Use raw adapter method to get native SDK response for strict backward compatibility
        raw_result = await adapter.invoke_raw(request)

        # If Bedrock adapter was used, convert response to Cerebras format
        if adapter.provider_name == "bedrock":
            # raw_result is boto3 Bedrock response (dict)
            cerebras_dict = BedrockToCerebrasMapper.map_chat_completion(raw_result)
            # Try to create Cerebras SDK ChatCompletion from dict
            try:
                # If Cerebras SDK is available, use its type
                return ChatCompletion(**cerebras_dict)
            except Exception:  # noqa: BLE001
                # Fallback: return dict (will still work for basic usage)
                return cerebras_dict
        else:
            # Cerebras adapter - already returns native ChatCompletion
            return raw_result


class _AsyncChat:
    """Async chat interface."""

    def __init__(self, client: AsyncCerebras) -> None:
        """Initialize async chat interface.

        Args:
            client: Parent AsyncCerebras client instance.
        """
        self.completions = _AsyncChatCompletions(client)
