"""AWS Bedrock adapter integration.

This adapter uses boto3 to interact with AWS Bedrock's Converse API for chat
completions and normalizes responses to the SDK's ``UnifiedChatResponse``
schema. Supports streaming when enabled.
"""

from __future__ import annotations

import asyncio
import time
import uuid
from collections.abc import AsyncIterator
from typing import Any, NoReturn, cast

from .._context import RequestContext
from .._exceptions import (
    AuthenticationError,
    InvalidRequestError,
    NotFoundError,
    PermissionDeniedError,
    ProviderError,
    RateLimitError,
    ServiceUnavailableError,
    map_http_status_to_exception,
)
from ..models.config import SDKConfig
from ..models.model import Model
from ..models.request import ChatRequest
from ..models.response import (
    Choice,
    UnifiedChatResponse,
    Usage,
)
from ..models.stream import StreamChunk
from .base import BaseAdapter
from .mappers import BedrockResponseMapper

# Bedrock Converse API response type
# This is the native boto3 response dict format
BedrockConverseResponse = dict[str, Any]

try:  # pragma: no cover - import availability depends on environment
    import boto3
except Exception:  # noqa: BLE001
    boto3 = None


class BedrockAdapter(BaseAdapter):
    """AWS Bedrock adapter for chat completions using the Converse API.

    Args:
        max_concurrent: Maximum concurrent requests (default 5 for AWS rate limits).
        credentials: Optional dict with 'aws_access_key_id', 'aws_secret_access_key',
            'aws_session_token', and 'region_name'. Falls back to environment/IAM.
    """

    def __init__(
        self,
        max_concurrent: int = 5,
        *,
        credentials: dict[str, str] | None = None,
    ) -> None:
        super().__init__(max_concurrent=max_concurrent)
        self._bedrock_client: Any | None = None
        self._credentials = credentials or {}

    @property
    def provider_name(self) -> str:
        """Returns 'bedrock' as the provider identifier."""
        return "bedrock"

    async def invoke_raw(self, request: ChatRequest) -> BedrockConverseResponse:
        """Call AWS Bedrock Converse API and return raw provider response.

        This method returns the native boto3 Converse API response dict without any
        transformation. Use this for strict backward compatibility with existing
        Bedrock/boto3 code.

        Args:
            request: ChatRequest with model, messages, and optional parameters.

        Returns:
            BedrockConverseResponse: Native boto3 response dict

        Raises:
            AuthenticationError: If AWS credentials are invalid
            PermissionDeniedError: If access to model is denied
            NotFoundError: If model is not found
            RateLimitError: If rate limit is exceeded
            ServiceUnavailableError: If service is temporarily unavailable
            InvalidRequestError: If the request format is invalid
            ProviderError: For other provider-specific errors

        Example:
            >>> adapter = BedrockAdapter()
            >>> request = ChatRequest(...)
            >>> raw_response = await adapter.invoke_raw(request)
            >>> # raw_response is the native boto3 Converse API response dict
        """
        # Generate request ID for tracking
        ctx = RequestContext.new()
        request_id = ctx.correlation_id

        client = await self._get_or_create_client()

        # Convert messages to Bedrock format
        bedrock_messages = self._convert_messages_to_bedrock(request.messages)

        try:
            # Bedrock uses boto3, which is synchronous; run in thread
            def _call() -> dict[str, Any]:
                response = client.converse(
                    modelId=request.model,
                    messages=bedrock_messages,
                )
                return cast(dict[str, Any], response)

            raw: dict[str, Any] = await asyncio.to_thread(_call)
            return raw
        except Exception as exc:  # noqa: BLE001
            self._handle_bedrock_error(exc, request_id, request.model)

    def _handle_bedrock_error(self, exc: Exception, request_id: str, model: str) -> NoReturn:
        """Handle Bedrock API errors and map to our exception taxonomy.

        Args:
            exc: The exception raised by boto3
            request_id: Request ID for tracking
            model: Model identifier

        Raises:
            Appropriate SDK exception based on error type
        """
        message = str(exc).lower()
        error_type = type(exc).__name__

        # Extract HTTP status code from boto3 exceptions if available
        status_code = None
        if hasattr(exc, "response") and isinstance(
            exc.response, dict
        ):  # pyright: ignore[reportAttributeAccessIssue]
            status_code = exc.response.get("ResponseMetadata", {}).get(
                "HTTPStatusCode"
            )  # pyright: ignore[reportAttributeAccessIssue]

        # Authentication errors (401 - Unauthorized)
        if "credentials" in message or "unauthorized" in message:
            raise AuthenticationError(
                provider=self.provider_name,
                message="Invalid or missing AWS credentials",
                original_error=exc,
                request_id=request_id,
                status_code=status_code or 401,
            ) from exc

        # Permission denied errors (403 - Forbidden)
        if "accessdenied" in error_type.lower() or "forbidden" in message:
            raise PermissionDeniedError(
                provider=self.provider_name,
                message=f"Access denied to model '{model}'",
                original_error=exc,
                request_id=request_id,
                status_code=status_code or 403,
            ) from exc

        # Model not found errors (404)
        if "modelnotfound" in error_type.lower() or ("model" in message and "not found" in message):
            raise NotFoundError(
                provider=self.provider_name,
                message=f"Model '{model}' not found in Bedrock",
                original_error=exc,
                request_id=request_id,
                status_code=status_code or 404,
            ) from exc

        # Validation errors (400/422)
        if "validationexception" in error_type.lower() or "invalid" in message:
            raise InvalidRequestError(
                message=str(exc),
                request_id=request_id,
            ) from exc

        # Rate limiting (429)
        if "throttling" in error_type.lower() or "throttled" in message:
            # Try to extract retry_after from exception
            retry_after = None
            if hasattr(exc, "response") and isinstance(
                exc.response, dict
            ):  # pyright: ignore[reportAttributeAccessIssue]
                headers = exc.response.get("ResponseMetadata", {}).get(
                    "HTTPHeaders", {}
                )  # pyright: ignore[reportAttributeAccessIssue]
                retry_after_str = headers.get("Retry-After") or headers.get("retry-after")
                if retry_after_str:
                    try:
                        retry_after = int(retry_after_str)
                    except ValueError:
                        pass

            raise RateLimitError(
                provider=self.provider_name,
                message="Rate limit exceeded",
                original_error=exc,
                request_id=request_id,
                status_code=status_code or 429,
                retry_after=retry_after,
            ) from exc

        # Service unavailable (503)
        if "serviceunavailable" in error_type.lower() or "unavailable" in message:
            raise ServiceUnavailableError(
                provider=self.provider_name,
                message="Bedrock service temporarily unavailable",
                original_error=exc,
                request_id=request_id,
                status_code=status_code or 503,
            ) from exc

        # Map by HTTP status code if available
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

    async def invoke(self, request: ChatRequest) -> UnifiedChatResponse:
        """Call AWS Bedrock Converse API and normalize to UnifiedChatResponse.

        This method transforms the provider response into our unified OpenAI-compatible
        format. Use this for cross-provider functionality.

        Args:
            request: ChatRequest with model, messages, and optional parameters.

        Returns:
            UnifiedChatResponse: Normalized response with metrics

        Example:
            >>> adapter = BedrockAdapter()
            >>> request = ChatRequest(...)
            >>> unified_response = await adapter.invoke(request)
            >>> # unified_response is UnifiedChatResponse
        """
        started_perf = time.perf_counter()
        started_epoch = int(time.time())

        # Get raw response from provider
        raw = await self.invoke_raw(request)

        duration_ms = (time.perf_counter() - started_perf) * 1000.0

        # Use mapper to convert to unified format
        return BedrockResponseMapper.map_to_unified(
            raw,
            duration_ms=duration_ms,
            started_epoch=started_epoch,
            model=request.model,
        )

    async def invoke_streaming(self, request: ChatRequest) -> AsyncIterator[StreamChunk]:
        """Stream tokens from AWS Bedrock using ConverseStream API.

        Args:
            request: ChatRequest with model and messages.

        Yields:
            StreamChunk objects with delta content.
        """
        client = await self._get_or_create_client()
        bedrock_messages = self._convert_messages_to_bedrock(request.messages)

        try:

            def _call_stream() -> Any:
                response = client.converse_stream(
                    modelId=request.model,
                    messages=bedrock_messages,
                )
                return response

            stream_response = await asyncio.to_thread(_call_stream)

            # Process the event stream
            idx = 0
            request_id = f"bedrock-{uuid.uuid4()}"

            def _iterate_stream() -> list[dict[str, Any]]:
                events = []
                stream = stream_response.get("stream", [])
                for event in stream:
                    events.append(event)
                return events

            events = await asyncio.to_thread(_iterate_stream)

            for event in events:
                if "contentBlockDelta" in event:
                    delta = event["contentBlockDelta"].get("delta", {})
                    if "text" in delta:
                        text = delta["text"]
                        yield StreamChunk(
                            id=request_id,
                            model=request.model,
                            index=idx,
                            delta={"role": "assistant", "content": text},
                        )
                        idx += 1

            # Final stop chunk
            yield StreamChunk(
                id=request_id,
                model=request.model,
                index=idx,
                delta={"role": "assistant", "content": ""},
                finish_reason="stop",
            )

        except Exception:  # noqa: BLE001
            # Fallback to non-streaming if streaming fails
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
        """Check if the Bedrock client can be created and is healthy.

        Returns:
            Dict with 'status' ('healthy' or 'unhealthy') and 'provider'.
        """
        try:
            await self._get_or_create_client()
            return {"status": "healthy", "provider": self.provider_name}
        except Exception:  # noqa: BLE001
            return {"status": "unhealthy", "provider": self.provider_name}

    async def list_models_raw(self) -> dict[str, Any]:
        """List available models from AWS Bedrock and return raw boto3 response.

        Returns the native boto3 list_foundation_models() response without transformation.
        Use this for strict backward compatibility with boto3 bedrock client.

        Returns:
            dict: Native boto3 response with 'modelSummaries' key.

        Raises:
            ProviderError: If boto3 is not installed or API call fails.

        Example:
            >>> adapter = BedrockAdapter()
            >>> raw_response = await adapter.list_models_raw()
            >>> for model in raw_response['modelSummaries']:
            ...     print(model['modelId'])
        """
        if boto3 is None:
            raise ProviderError(
                provider=self.provider_name,
                message="boto3 is not installed",
                original_error=None,
            )

        # Get resolved credentials
        session_kwargs = self._get_credentials()

        # Create bedrock client (not bedrock-runtime) for listing models
        def _list_models() -> dict[str, Any]:
            session = boto3.Session(**session_kwargs)
            bedrock = session.client("bedrock")
            response = bedrock.list_foundation_models()
            return cast(dict[str, Any], response)

        response = await asyncio.to_thread(_list_models)
        return response

    async def list_models(self) -> list[Model]:
        """List available models from AWS Bedrock.

        Attempts to fetch models dynamically from AWS Bedrock API.
        Falls back to a static list if API call fails.

        This method transforms the native response into our unified Model format.

        Returns:
            list[Model]: List of available Bedrock models.
        """
        if boto3 is None:
            # boto3 not installed, return fallback list
            return self._get_fallback_models()

        try:
            # Get raw response from provider
            response = await self.list_models_raw()
            summaries = response.get("modelSummaries", [])

            # Get resolved credentials for detailed model info
            session_kwargs = self._get_credentials()
            session = boto3.Session(**session_kwargs)
            bedrock = session.client("bedrock")

            all_models = []
            converse_models = []
            for summary in summaries:
                # Only include models that support Converse API
                if (
                    len(summary.get("inputModalities", [])) == 1
                    and "TEXT" in summary.get("inputModalities", [])
                    and "TEXT" in summary.get("outputModalities", [])
                ):
                    all_models.append(
                        Model(
                            id=summary["modelId"],
                            object="model",
                            created=1704067200,  # Approximate Bedrock GA date
                            owned_by=summary.get("providerName", "aws").lower(),
                        )
                    )
            for model in all_models:
                model_id = model.id  # Access attribute, not dict key
                details = bedrock.get_foundation_model(modelIdentifier=model_id)
                capabilities = details["modelDetails"]["inferenceTypesSupported"]
                if "CONVERSE" in capabilities:
                    converse_models.append(model)

            return converse_models if converse_models else self._get_fallback_models()

        except Exception:  # noqa: BLE001
            # Fallback to static list if API call fails
            return self._get_fallback_models()

    def _get_fallback_models(self) -> list[Model]:
        """Return static list of common Bedrock models."""
        return [
            Model(
                id="qwen.qwen3-32b-v1:0",
                object="model",
                created=1735689600,  # January 2025
                owned_by="qwen",
            ),
            Model(
                id="anthropic.claude-3-haiku-20240307-v1:0",
                object="model",
                created=1709769600,  # March 2024
                owned_by="anthropic",
            ),
            Model(
                id="anthropic.claude-3-sonnet-20240229-v1:0",
                object="model",
                created=1709251200,  # February 2024
                owned_by="anthropic",
            ),
            Model(
                id="anthropic.claude-3-5-sonnet-20240620-v1:0",
                object="model",
                created=1718841600,  # June 2024
                owned_by="anthropic",
            ),
            Model(
                id="meta.llama3-70b-instruct-v1:0",
                object="model",
                created=1713398400,  # April 2024
                owned_by="meta",
            ),
        ]

    def _get_credentials(self) -> dict[str, str]:
        """Get AWS credentials with precedence: provided > environment > IAM.

        Returns:
            dict[str, str]: Resolved credentials with keys for boto3 Session.
        """
        cfg = SDKConfig.load()

        # Resolve each credential with fallback chain
        aws_access_key_id = (
            self._credentials.get("aws_access_key_id")
            or cfg.aws_access_key_id.get_secret_value()
            or None
        )
        aws_secret_access_key = (
            self._credentials.get("aws_secret_access_key")
            or cfg.aws_secret_access_key.get_secret_value()
            or None
        )
        aws_session_token = (
            self._credentials.get("aws_session_token")
            or cfg.aws_session_token.get_secret_value()
            or None
        )
        region_name = self._credentials.get("region_name") or cfg.aws_region

        # Build session kwargs (only include non-None values)
        session_kwargs: dict[str, str] = {"region_name": region_name}
        if aws_access_key_id:
            session_kwargs["aws_access_key_id"] = aws_access_key_id
        if aws_secret_access_key:
            session_kwargs["aws_secret_access_key"] = aws_secret_access_key
        if aws_session_token:
            session_kwargs["aws_session_token"] = aws_session_token

        return session_kwargs

    async def _get_or_create_client(self) -> Any:
        """Create or reuse AWS Bedrock client using boto3.

        Returns:
            boto3 bedrock-runtime client.

        Raises:
            ProviderError: If boto3 is not installed.
            AuthenticationError: If AWS credentials are missing.
        """
        if self._bedrock_client is not None:
            return self._bedrock_client

        if boto3 is None:
            raise ProviderError(
                provider=self.provider_name,
                original_error=ImportError("boto3 not installed. Run `pip install boto3`"),
            )

        # Get resolved credentials
        session_kwargs = self._get_credentials()

        # Create boto3 session (supports env vars and IAM roles automatically)
        session = boto3.Session(**session_kwargs)
        self._bedrock_client = session.client("bedrock-runtime")

        return self._bedrock_client

    def _convert_messages_to_bedrock(self, messages: list[Any]) -> list[dict[str, Any]]:
        """Convert UnifiedAI messages to Bedrock Converse API format.

        Args:
            messages: List of Message objects.

        Returns:
            List of Bedrock-formatted message dicts.
        """
        bedrock_messages = []
        for msg in messages:
            msg_dict = msg.model_dump() if hasattr(msg, "model_dump") else msg
            role = msg_dict.get("role", "user")
            content = msg_dict.get("content", "")

            # Bedrock uses 'user' and 'assistant' roles
            if role == "system":
                # Bedrock handles system messages separately; for now, prepend to first user message
                continue

            bedrock_messages.append({"role": role, "content": [{"text": content}]})

        return bedrock_messages

    def _normalize_response(
        self,
        *,
        raw: dict[str, Any],
        fallback_id: str,
        created: int,
        model: str,
    ) -> UnifiedChatResponse:
        """Normalize Bedrock Converse API response to UnifiedChatResponse.

        Args:
            raw: Raw Bedrock API response from converse().
            fallback_id: ID to use if not present in response.
            created: Timestamp for response creation.
            model: Model name.

        Returns:
            UnifiedChatResponse object.
        """
        # Extract output from Bedrock response
        output = raw.get("output", {})
        message_data = output.get("message", {})
        content_blocks = message_data.get("content", [])

        # Extract text from content blocks (Converse API returns list of content blocks)
        text_content = ""
        for block in content_blocks:
            if "text" in block:
                text_content += block["text"]

        # Extract usage (Bedrock returns inputTokens, outputTokens, totalTokens)
        usage_data = raw.get("usage", {})
        usage = Usage(
            prompt_tokens=int(usage_data.get("inputTokens", 0)),
            completion_tokens=int(usage_data.get("outputTokens", 0)),
            total_tokens=int(usage_data.get("totalTokens", 0)),
        )

        # Get stop reason (Bedrock uses stopReason field)
        stop_reason = raw.get("stopReason", "end_turn")
        # Map Bedrock stop reasons to OpenAI-compatible ones
        stop_reason_map = {
            "end_turn": "stop",
            "max_tokens": "length",
            "stop_sequence": "stop",
            "content_filtered": "content_filter",
        }
        finish_reason = stop_reason_map.get(stop_reason, stop_reason)

        return UnifiedChatResponse(
            id=str(raw.get("ResponseMetadata", {}).get("RequestId", fallback_id)),
            object="chat.completion",
            created=created,
            model=model,
            choices=[
                Choice(
                    index=0,
                    message={
                        "role": "assistant",
                        "content": text_content,
                    },
                    finish_reason=finish_reason,
                )
            ],
            usage=usage,
        )
