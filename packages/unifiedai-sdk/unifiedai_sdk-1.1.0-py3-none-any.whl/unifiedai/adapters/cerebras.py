"""Cerebras adapter integration.

This adapter uses the official Cerebras Cloud Python SDK to perform chat
completions and normalizes responses to the SDK's ``UnifiedChatResponse``
schema. Streaming is supported when the Cerebras SDK exposes a streaming API;
otherwise, a single terminal chunk is yielded.
"""

from __future__ import annotations

import asyncio
import re
import time
from collections.abc import AsyncIterator
from typing import Any, NoReturn, cast

from cerebras.cloud.sdk.types import ModelListResponse  # type: ignore[import-not-found]

from .._context import RequestContext
from .._exceptions import (
    AuthenticationError,
    InvalidRequestError,
    NotFoundError,
    ProviderError,
    map_http_status_to_exception,
)
from ..models.config import SDKConfig
from ..models.model import Model
from ..models.request import ChatRequest
from ..models.response import (
    Choice,
    ProviderMetadata,
    ResponseMetrics,
    UnifiedChatResponse,
    Usage,
)
from ..models.stream import StreamChunk
from .base import BaseAdapter
from .mappers import CerebrasResponseMapper

# Import Cerebras SDK response types for strict backward compatibility
# Use type alias for flexibility
ChatCompletion: Any
try:
    from cerebras.cloud.sdk.types import (
        ChatCompletion as _ChatCompletion,
    )

    ChatCompletion = _ChatCompletion
except (ImportError, AttributeError):
    ChatCompletion = Any  # Fallback type

# Optional import; we keep a constructor reference to avoid mypy "assign to type" issues
CerebrasCtor: Any
AsyncCerebrasCtor: Any
try:  # pragma: no cover - import availability depends on environment
    from cerebras.cloud.sdk import (  # type: ignore[import-not-found]
        AsyncCerebras as _AsyncCerebras,
    )
    from cerebras.cloud.sdk import (
        Cerebras as _Cerebras,
    )

    CerebrasCtor = _Cerebras
    AsyncCerebrasCtor = _AsyncCerebras
except Exception:  # noqa: BLE001
    CerebrasCtor = None
    AsyncCerebrasCtor = None


class CerebrasAdapter(BaseAdapter):
    def __init__(
        self,
        max_concurrent: int = 10,
        *,
        credentials: dict[str, str] | None = None,
        return_reasoning: bool = True,
    ) -> None:
        super().__init__(max_concurrent=max_concurrent)
        self._cb_client: Any | None = None
        self._cb_async_client: Any | None = None
        self._credentials = credentials or {}
        self._return_reasoning = return_reasoning

    @property
    def provider_name(self) -> str:
        return "cerebras"

    def _handle_provider_error(self, exc: Exception, request_id: str) -> NoReturn:
        """Handle and map provider exceptions to SDK error types.

        Args:
            exc: The caught exception from provider
            request_id: Request correlation ID for tracking

        Raises:
            Appropriate SDK error type based on exception
        """
        message = str(exc).lower()

        # Authentication errors (401)
        if "api key" in message or "unauthoriz" in message or "401" in message:
            raise AuthenticationError(
                provider=self.provider_name,
                message="Invalid or missing API key",
                original_error=exc,
                request_id=request_id,
                status_code=401,
            ) from exc

        # Model not found errors (404)
        if "model" in message and ("not found" in message or "404" in message):
            raise NotFoundError(
                provider=self.provider_name,
                message="Model not found",
                original_error=exc,
                request_id=request_id,
                status_code=404,
            ) from exc

        # Invalid request errors (400, 422)
        if "invalid" in message or "bad request" in message or "400" in message or "422" in message:
            raise InvalidRequestError(message=str(exc), request_id=request_id) from exc

        # Try to extract HTTP status code from exception
        status_code = None
        if hasattr(exc, "status_code"):
            status_code = exc.status_code
        elif hasattr(exc, "status"):
            status_code = exc.status

        # Map to specific error type if status code is known
        if status_code:
            raise map_http_status_to_exception(
                status_code=status_code,
                provider=self.provider_name,
                message=str(exc),
                request_id=request_id,
                original_error=exc,
            ) from exc

        # Generic provider error with request_id
        raise ProviderError(
            provider=self.provider_name,
            message=str(exc),
            original_error=exc,
            request_id=request_id,
        ) from exc

    def _process_response(
        self,
        raw: dict[str, Any],
        request: ChatRequest,
        started_epoch: int,
        duration_ms: float,
    ) -> UnifiedChatResponse:
        """Process raw provider response into UnifiedChatResponse with metrics.

        Args:
            raw: Raw response dict from provider
            request: Original request
            started_epoch: Request start timestamp
            duration_ms: Client-measured duration in milliseconds

        Returns:
            Normalized UnifiedChatResponse with metrics
        """
        reasoning, cleaned = self._extract_reasoning_and_answer(raw)

        unified = self._normalize_response(
            raw=raw,
            fallback_id=raw.get("id") or "cb-unknown",
            created=raw.get("created") or started_epoch,
            model=request.model,
            override_content=cleaned,
        )

        # Extract Cerebras-provided timing metrics (if available)
        # We pass through provider data as-is, without calculation or estimation
        time_info = raw.get("time_info")
        provider_time_info: dict[str, float | int] | None = None

        if time_info and isinstance(time_info, dict):
            # Only include if provider actually sent time_info
            # Convert milliseconds to same format for consistency
            provider_time_info = {}
            for key, value in time_info.items():
                if not isinstance(key, str):
                    continue
                try:
                    if value is not None:  # Skip None values
                        # Convert to float or int
                        num_val = float(value)
                        provider_time_info[key] = int(num_val) if num_val.is_integer() else num_val
                except (ValueError, TypeError):
                    # Skip non-numeric values
                    pass

        # Create metrics with ONLY SDK-measured duration and provider-supplied time_info
        unified.metrics = ResponseMetrics(
            duration_ms=duration_ms,
            provider_time_info=provider_time_info,
        )

        meta_raw = dict(raw)
        if self._return_reasoning and reasoning:
            meta_raw["reasoning"] = reasoning
        unified.provider_metadata = ProviderMetadata(provider=self.provider_name, raw=meta_raw)
        return unified

    def invoke_raw_sync(self, request: ChatRequest) -> ChatCompletion:
        """Call Cerebras chat API synchronously and return raw provider response.

        This method returns the native Cerebras SDK response type without any
        transformation. Use this for strict backward compatibility in synchronous contexts.

        Args:
            request: Chat completion request

        Returns:
            ChatCompletion: Native Cerebras SDK response object

        Raises:
            AuthenticationError: If API key is invalid
            InvalidRequestError: If request parameters are invalid
            ProviderError: For other provider-specific errors

        Example:
            >>> adapter = CerebrasAdapter()
            >>> request = ChatRequest(...)
            >>> raw_response = adapter.invoke_raw_sync(request)
            >>> # raw_response is cerebras.cloud.sdk.types.ChatCompletion
        """
        # Generate request ID for tracking
        ctx = RequestContext.new()
        request_id = ctx.correlation_id

        # Use sync client - run in current thread, no event loop needed
        loop = asyncio.new_event_loop()
        try:
            sync_client = loop.run_until_complete(self._get_or_create_client())
        finally:
            loop.close()

        try:
            # Use synchronous Cerebras client - return as-is
            resp = sync_client.chat.completions.create(
                model=request.model,
                messages=[m.model_dump() for m in request.messages],
            )
            return resp
        except Exception as exc:  # noqa: BLE001
            self._handle_provider_error(exc, request_id)

    def invoke_sync(self, request: ChatRequest) -> UnifiedChatResponse:
        """Call Cerebras chat API synchronously and normalize to UnifiedChatResponse.

        This method uses the synchronous Cerebras client and transforms the response
        into our unified OpenAI-compatible format. Use this for cross-provider
        functionality in synchronous contexts.

        Args:
            request: Chat completion request

        Returns:
            UnifiedChatResponse: Normalized response with metrics

        Example:
            >>> adapter = CerebrasAdapter()
            >>> request = ChatRequest(...)
            >>> unified_response = adapter.invoke_sync(request)
            >>> # unified_response is UnifiedChatResponse
        """
        started_perf = time.perf_counter()
        started_epoch = int(time.time())

        # Get raw response from provider
        raw_resp = self.invoke_raw_sync(request)

        # Convert to dict for mapper
        if hasattr(raw_resp, "model_dump"):
            raw = raw_resp.model_dump()
        else:
            raw = dict(raw_resp)

        duration_ms = (time.perf_counter() - started_perf) * 1000.0

        # Use mapper to convert to unified format
        return CerebrasResponseMapper.map_to_unified(
            raw,
            duration_ms=duration_ms,
            started_epoch=started_epoch,
            model=request.model,
            extract_reasoning=self._return_reasoning,
        )

    async def invoke_raw(self, request: ChatRequest) -> ChatCompletion:
        """Call Cerebras chat API and return raw provider response.

        This method returns the native Cerebras SDK response type without any
        transformation. Use this for strict backward compatibility with existing
        Cerebras SDK code.

        Args:
            request: Chat completion request

        Returns:
            ChatCompletion: Native Cerebras SDK response object

        Raises:
            AuthenticationError: If API key is invalid
            InvalidRequestError: If request parameters are invalid
            ProviderError: For other provider-specific errors

        Example:
            >>> adapter = CerebrasAdapter()
            >>> request = ChatRequest(...)
            >>> raw_response = await adapter.invoke_raw(request)
            >>> # raw_response is cerebras.cloud.sdk.types.ChatCompletion
        """
        # Generate request ID for tracking
        ctx = RequestContext.new()
        request_id = ctx.correlation_id

        async_client = await self._get_or_create_async_client()

        try:
            # Use native async Cerebras client - return as-is
            resp = await async_client.chat.completions.create(
                model=request.model,
                messages=[m.model_dump() for m in request.messages],
            )
            return resp
        except Exception as exc:  # noqa: BLE001
            self._handle_provider_error(exc, request_id)

    async def invoke(self, request: ChatRequest) -> UnifiedChatResponse:
        """Call Cerebras chat API asynchronously and normalize to UnifiedChatResponse.

        This method transforms the provider response into our unified OpenAI-compatible
        format. Use this for cross-provider functionality.

        Args:
            request: Chat completion request

        Returns:
            UnifiedChatResponse: Normalized response with metrics

        Example:
            >>> adapter = CerebrasAdapter()
            >>> request = ChatRequest(...)
            >>> unified_response = await adapter.invoke(request)
            >>> # unified_response is UnifiedChatResponse
        """
        started_perf = time.perf_counter()
        started_epoch = int(time.time())

        # Get raw response from provider
        raw_resp = await self.invoke_raw(request)

        # Convert to dict for mapper
        if hasattr(raw_resp, "model_dump"):
            raw = raw_resp.model_dump()
        else:
            raw = dict(raw_resp)

        duration_ms = (time.perf_counter() - started_perf) * 1000.0

        # Use mapper to convert to unified format
        return CerebrasResponseMapper.map_to_unified(
            raw,
            duration_ms=duration_ms,
            started_epoch=started_epoch,
            model=request.model,
            extract_reasoning=self._return_reasoning,
        )

    async def invoke_streaming(self, request: ChatRequest) -> AsyncIterator[StreamChunk]:
        """Stream tokens from Cerebras if SDK supports streaming; else one-shot.

        If streaming isn't supported, yields a single terminal chunk built from
        the non-streaming ``invoke`` result.
        """
        client = await self._get_or_create_client()

        # If the SDK exposes a streaming flag/iterator, use it; otherwise fallback.
        if callable(getattr(client.chat.completions, "create", None)):
            try:
                # Attempt to use a streaming mode if available
                def _call_stream() -> list[dict[str, Any]]:
                    # Many SDKs yield chunks when stream=True; coalesce here to simplify
                    stream_resp = client.chat.completions.create(
                        model=request.model,
                        messages=[m.model_dump() for m in request.messages],
                        stream=True,
                    )
                    chunks: list[dict[str, Any]] = []
                    for ev in stream_resp:
                        item = ev.model_dump() if hasattr(ev, "model_dump") else ev
                        chunks.append(cast(dict[str, Any], item))
                    return chunks

                chunks = await asyncio.to_thread(_call_stream)
                idx = 0
                for ev in chunks:
                    delta_text = (((ev.get("choices") or [{}])[0]).get("delta") or {}).get(
                        "content"
                    ) or ""
                    if delta_text:
                        yield StreamChunk(
                            id=str(ev.get("id") or "cb-unknown"),
                            model=request.model,
                            index=idx,
                            delta={"role": "assistant", "content": delta_text},
                        )
                        idx += 1
                yield StreamChunk(
                    id=str((chunks[-1] if chunks else {}).get("id") or "cb-unknown"),
                    model=request.model,
                    index=idx,
                    delta={"role": "assistant", "content": ""},
                    finish_reason="stop",
                )
                return
            except Exception:
                # Fallback to non-streaming if streaming path fails
                pass

        # Fallback: one-shot invoke() then emit a single stop chunk
        resp = await self.invoke(request)
        content = (resp.choices[0].message.get("content") if resp.choices else "") or ""
        yield StreamChunk(
            id=resp.id,
            model=request.model,
            index=0,
            delta={"role": "assistant", "content": content},
            finish_reason="stop",
        )

    async def health_check(self) -> dict[str, str]:
        """Check if the Cerebras client can be created and is healthy.

        Returns:
            Dict with 'status' ('healthy' or 'unhealthy') and 'provider'.
        """
        try:
            await self._get_or_create_client()
            return {"status": "healthy", "provider": self.provider_name}
        except Exception:  # noqa: BLE001
            return {"status": "unhealthy", "provider": self.provider_name}

    async def list_models_raw(self) -> ModelListResponse:
        """List available models from Cerebras and return raw SDK response.

        Returns the native Cerebras SDK ModelListResponse without any transformation.
        Use this for strict backward compatibility with Cerebras SDK.

        Returns:
            ModelListResponse: Native Cerebras SDK response type with .data attribute.

        Raises:
            ProviderError: If the API call fails.

        Example:
            >>> adapter = CerebrasAdapter()
            >>> raw_response = await adapter.list_models_raw()
            >>> # raw_response is cerebras.cloud.sdk.types.ModelListResponse
            >>> for model in raw_response.data:
            ...     print(model.id)
        """
        async_client = await self._get_or_create_async_client()

        # Call Cerebras SDK's async models.list() API - return as-is
        response = await async_client.models.list()
        return response

    async def list_models(self) -> list[Model]:
        """List available models from Cerebras using the SDK's models API.

        Calls the Cerebras SDK's `client.models.list()` to get the current list
        of available models. Falls back to a static list if the API call fails.

        This method transforms the native response into our unified Model format.

        Returns:
            list[Model]: List of available Cerebras models.
        """
        try:
            # Get raw response from provider
            response = await self.list_models_raw()

            # Response format: {"object": "list", "data": [{model objects}]}
            if hasattr(response, "data"):
                # SDK returns a structured response
                models_data: list[dict[str, Any]] = [
                    model.model_dump() if hasattr(model, "model_dump") else dict(model)
                    for model in response.data
                ]
            elif isinstance(response, dict) and "data" in response:
                # Direct dict response
                models_data = cast(list[dict[str, Any]], response["data"])
            else:
                models_data = []

            # Convert to our Model format
            models = []
            for model_dict in models_data:
                models.append(
                    Model(
                        id=model_dict.get("id", ""),
                        object="model",
                        created=model_dict.get("created", 0),
                        owned_by=model_dict.get("owned_by", "cerebras"),
                    )
                )

            return models if models else self._get_fallback_models()

        except Exception:  # noqa: BLE001
            # Fallback to static list if API call fails
            return self._get_fallback_models()

    def _get_fallback_models(self) -> list[Model]:
        """Return static list of common Cerebras models as fallback."""
        return [
            Model(
                id="llama3.1-8b",
                object="model",
                created=1721692800,
                owned_by="Meta",
            ),
            Model(
                id="llama3.1-70b",
                object="model",
                created=1721692800,
                owned_by="Meta",
            ),
            Model(
                id="llama-3.3-70b",
                object="model",
                created=1733443200,
                owned_by="Meta",
            ),
            Model(
                id="llama-4-scout-17b-16e-instruct",
                object="model",
                created=1735689600,
                owned_by="Meta",
            ),
            Model(
                id="qwen-3-32b",
                object="model",
                created=1735689600,
                owned_by="Qwen",
            ),
            Model(
                id="gpt-oss-120b",
                object="model",
                created=1735689600,
                owned_by="cerebras",
            ),
        ]

    async def _get_or_create_client(self) -> Any:
        """Create or reuse a Cerebras SDK sync client using SDKConfig secrets."""
        if self._cb_client is not None:
            return self._cb_client
        if CerebrasCtor is None:
            raise ProviderError(
                provider=self.provider_name,
                original_error=ImportError(
                    "cerebras-cloud SDK not installed. Run `pip install cerebras-cloud-sdk`"
                ),
            )
        # Precedence: provided credentials > env config
        api_key = self._credentials.get("api_key")
        if not api_key:
            cfg = SDKConfig.load()
            api_key = cfg.cerebras_key.get_secret_value()
        if not api_key:
            raise AuthenticationError(
                provider=self.provider_name,
                message="Missing CEREBRAS_API_KEY environment variable",
                status_code=401,
            ) from None
        # The Cerebras SDK sync client; construct once and reuse
        self._cb_client = CerebrasCtor(api_key=api_key)
        return self._cb_client

    async def _get_or_create_async_client(self) -> Any:
        """Create or reuse a Cerebras SDK async client using SDKConfig secrets."""
        if self._cb_async_client is not None:
            return self._cb_async_client
        if AsyncCerebrasCtor is None:
            raise ProviderError(
                provider=self.provider_name,
                original_error=ImportError(
                    "cerebras-cloud SDK not installed. Run `pip install cerebras-cloud-sdk`"
                ),
            )
        # Precedence: provided credentials > env config
        api_key = self._credentials.get("api_key")
        if not api_key:
            cfg = SDKConfig.load()
            api_key = cfg.cerebras_key.get_secret_value()
        if not api_key:
            raise AuthenticationError(
                provider=self.provider_name,
                message="Missing CEREBRAS_API_KEY environment variable",
                status_code=401,
            ) from None
        # The Cerebras SDK async client; construct once and reuse
        self._cb_async_client = AsyncCerebrasCtor(api_key=api_key)
        return self._cb_async_client

    def _normalize_response(
        self,
        *,
        raw: dict[str, Any],
        fallback_id: str,
        created: int,
        model: str,
        override_content: str | None = None,
    ) -> UnifiedChatResponse:
        """Normalize Cerebras response dict to UnifiedChatResponse."""
        # Choices/message extraction with fallbacks
        choices_raw = raw.get("choices") or []
        first = choices_raw[0] if choices_raw else {}
        message = first.get("message") or {"role": "assistant", "content": first.get("text") or ""}
        if override_content is not None:
            message = {
                "role": str(message.get("role") or "assistant"),
                "content": override_content,
            }

        usage = raw.get("usage") or {}
        u = Usage(
            prompt_tokens=int(usage.get("prompt_tokens") or 0),
            completion_tokens=int(usage.get("completion_tokens") or 0),
            total_tokens=int(usage.get("total_tokens") or 0),
        )

        unified = UnifiedChatResponse(
            id=str(raw.get("id") or fallback_id),
            object="chat.completion",
            created=int(raw.get("created") or created),
            model=str(raw.get("model") or model),
            choices=[
                Choice(
                    index=int(first.get("index") or 0),
                    message={
                        "role": str(message.get("role") or "assistant"),
                        "content": str(message.get("content") or ""),
                    },
                    finish_reason=(first.get("finish_reason")),
                )
            ],
            usage=u,
        )
        return unified

    def _extract_reasoning_and_answer(self, raw: dict[str, Any]) -> tuple[str | None, str]:
        """Extract <think>...</think> as reasoning and return cleaned answer.

        Returns (reasoning_or_None, cleaned_content).
        """
        text: str = ""
        try:
            choices = raw.get("choices") or []
            if choices:
                first = choices[0]
                msg = first.get("message") or {}
                text = msg.get("content") or first.get("text") or ""
        except Exception:  # noqa: BLE001
            text = ""

        if not isinstance(text, str):
            text = str(text)

        m = re.search(r"<think>(.*?)</think>", text, flags=re.DOTALL | re.IGNORECASE)
        reasoning = m.group(1).strip() if m else None
        cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE).strip()
        return reasoning, cleaned
