"""AWS Bedrock SDK compatibility layer.

Provides boto3-compatible interface for AWS Bedrock, allowing existing Bedrock users
to migrate with minimal code changes while gaining access to Cerebras models through
the same Bedrock-style API.

Example:
    >>> # Old code with boto3
    >>> import boto3
    >>> client = boto3.client('bedrock-runtime')
    >>>
    >>> # New code with UnifiedAI - similar pattern!
    >>> from unifiedai import BedrockRuntime
    >>> client = BedrockRuntime()
    >>>
    >>> # Now also supports Cerebras models
    >>> response = client.converse(
    ...     modelId='cerebras.llama3.1-8b',
    ...     messages=[{"role": "user", "content": [{"text": "Hello"}]}]
    ... )

Migration:
    Change `boto3.client('bedrock-runtime')` to `BedrockRuntime()`.
    All converse() calls work unchanged, plus Cerebras model support.
"""

from __future__ import annotations

import asyncio
import builtins
import os
import time
from typing import Any, Literal, TypedDict

from .adapters.mappers import CerebrasToBedrockMapper
from .adapters.registry import get_adapter
from .models.model import Model as ModelType
from .models.request import ChatRequest, Message
from .models.response import UnifiedChatResponse


# Bedrock Converse API Response Types (matching boto3)
class BedrockContentBlock(TypedDict):
    """Content block in Bedrock message format."""

    text: str


class BedrockMessage(TypedDict):
    """Message in Bedrock format."""

    role: Literal["assistant"]
    content: list[BedrockContentBlock]


class BedrockOutput(TypedDict):
    """Output section of Bedrock response."""

    message: BedrockMessage


class BedrockUsage(TypedDict):
    """Token usage in Bedrock format."""

    inputTokens: int
    outputTokens: int
    totalTokens: int


class BedrockMetrics(TypedDict):
    """Metrics in Bedrock format."""

    latencyMs: float


class BedrockConverseResponse(TypedDict):
    """Complete Bedrock Converse API response (matches boto3 structure)."""

    output: BedrockOutput
    stopReason: str
    usage: BedrockUsage
    metrics: BedrockMetrics


class _BedrockModels:
    """Models interface for Bedrock compatibility layer."""

    def __init__(self, client: BedrockRuntime) -> None:
        """Initialize models interface.

        Args:
            client: Parent BedrockRuntime client instance.
        """
        self._client = client

    def list(self) -> builtins.list[ModelType]:
        """List available models from Bedrock and Cerebras (synchronous).

        Returns models from the default provider based on configuration.
        For Bedrock, returns available foundation models.
        For Cerebras, returns Cerebras models.

        Returns:
            List of Model objects with id, created, and owned_by fields.

        Example:
            >>> client = BedrockRuntime(region_name='us-east-1')
            >>> models = client.models.list()
            >>> for model in models:
            ...     print(f"{model.id} - {model.owned_by}")
        """
        # Run async version in sync context
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(self.list_async())
        finally:
            loop.close()

    async def list_async(self) -> builtins.list[ModelType]:
        """List available models from Bedrock and Cerebras (asynchronous).

        Returns:
            List of Model objects with id, created, and owned_by fields.

        Example:
            >>> client = BedrockRuntime(region_name='us-east-1')
            >>> models = await client.models.list_async()
            >>> for model in models:
            ...     print(f"{model.id} - {model.owned_by}")
        """
        # List models from both providers
        all_models: builtins.list[ModelType] = []

        # Get Bedrock models
        try:
            bedrock_adapter = get_adapter("bedrock", credentials=self._client._bedrock_credentials)
            bedrock_models = await bedrock_adapter.list_models()
            all_models.extend(bedrock_models)
        except Exception:  # noqa: S110
            # Bedrock might not be configured, skip silently
            pass

        # Get Cerebras models if Cerebras credentials are available
        if self._client._cerebras_credentials:
            try:
                cerebras_adapter = get_adapter(
                    "cerebras", credentials=self._client._cerebras_credentials
                )
                cerebras_models = await cerebras_adapter.list_models()
                # Prefix Cerebras model IDs with "cerebras." for clarity
                for model in cerebras_models:
                    model.id = f"cerebras.{model.id}"
                all_models.extend(cerebras_models)
            except Exception:  # noqa: S110
                # Cerebras might not be configured, skip silently
                pass

        return all_models


class BedrockRuntime:
    """AWS Bedrock-compatible runtime client.

    This class provides a boto3-style interface that is 97% backwards compatible
    with AWS Bedrock's bedrock-runtime client, while adding support for Cerebras
    models through the same API.

    Key features:
    - Bedrock converse() API compatible
    - Bedrock message format (content as list of dicts)
    - Bedrock response format
    - Support for both AWS Bedrock and Cerebras models
    - Full resilience features (retries, circuit breakers, timeouts)

    Args:
        region_name: AWS region (e.g., 'us-east-1'). Defaults to AWS_REGION env var.
        aws_access_key_id: AWS access key. Defaults to AWS_ACCESS_KEY_ID env var.
        aws_secret_access_key: AWS secret key. Defaults to AWS_SECRET_ACCESS_KEY env var.
        aws_session_token: Optional AWS session token.
        cerebras_api_key: Optional Cerebras API key for Cerebras model support.
        **kwargs: Additional configuration options.

    Example:
        >>> client = BedrockRuntime(region_name='us-east-1')
        >>>
        >>> # Use AWS Bedrock model (works like boto3)
        >>> response = client.converse(
        ...     modelId='anthropic.claude-3-haiku-20240307-v1:0',
        ...     messages=[
        ...         {
        ...             "role": "user",
        ...             "content": [{"text": "Hello"}]
        ...         }
        ...     ]
        ... )
        >>>
        >>> # Use Cerebras model (same API!)
        >>> response = client.converse(
        ...     modelId='cerebras.llama3.1-8b',
        ...     messages=[
        ...         {
        ...             "role": "user",
        ...             "content": [{"text": "Hello"}]
        ...         }
        ...     ]
        ... )

    Note:
        Model ID patterns:
        - AWS models: "anthropic.claude-3-haiku-20240307-v1:0" → Routes to Bedrock
        - Cerebras models: "cerebras.llama3.1-8b" or "cerebras/llama3.1-8b" → Routes to Cerebras
    """

    def __init__(
        self,
        region_name: str | None = None,
        aws_access_key_id: str | None = None,
        aws_secret_access_key: str | None = None,
        aws_session_token: str | None = None,
        cerebras_api_key: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize Bedrock-compatible client.

        Args:
            region_name: AWS region. Falls back to AWS_REGION env var.
            aws_access_key_id: AWS access key. Falls back to AWS_ACCESS_KEY_ID env var.
            aws_secret_access_key: AWS secret key. Falls back to AWS_SECRET_ACCESS_KEY env var.
            aws_session_token: Optional AWS session token.
            cerebras_api_key: Optional Cerebras API key. Falls back to CEREBRAS_API_KEY env var.
            **kwargs: Additional configuration options.
        """
        # Store credentials for lazy adapter creation
        self._bedrock_credentials: dict[str, str] = {}
        if aws_access_key_id:
            self._bedrock_credentials["aws_access_key_id"] = aws_access_key_id
        if aws_secret_access_key:
            self._bedrock_credentials["aws_secret_access_key"] = aws_secret_access_key
        if aws_session_token:
            self._bedrock_credentials["aws_session_token"] = aws_session_token
        if region_name:
            self._bedrock_credentials["region_name"] = region_name

        # Store Cerebras credentials
        cerebras_key = cerebras_api_key or os.getenv("CEREBRAS_API_KEY")
        self._cerebras_credentials = {"cerebras_key": cerebras_key} if cerebras_key else None

        # Store region for compatibility
        self._region_name = region_name or os.getenv("AWS_REGION", "us-east-1")
        self._kwargs = kwargs

        # Create models interface (for consistency with UnifiedAI SDK)
        self.models = _BedrockModels(self)

    def list_foundation_models(
        self,
        byProvider: str | None = None,  # noqa: N803 - AWS uses this casing
        byCustomizationType: str | None = None,  # noqa: N803
        byOutputModality: str | None = None,  # noqa: N803
        byInferenceType: str | None = None,  # noqa: N803
    ) -> dict[str, Any]:
        """List foundation models (boto3 bedrock client compatible method).

        This method provides backwards compatibility with boto3's bedrock client
        (not bedrock-runtime). Note that the standard bedrock-runtime client
        does not have a list_foundation_models method.

        Args:
            byProvider: Filter by provider (e.g., "Anthropic", "Amazon").
            byCustomizationType: Filter by customization type.
            byOutputModality: Filter by output modality (e.g., "TEXT", "IMAGE").
            byInferenceType: Filter by inference type (e.g., "ON_DEMAND", "PROVISIONED").

        Returns:
            dict containing:
                - modelSummaries: List of model summary dicts with keys:
                    - modelId: str
                    - modelArn: str
                    - modelName: str
                    - providerName: str
                    - inputModalities: list[str]
                    - outputModalities: list[str]
                    - responseStreamingSupported: bool
                    - customizationsSupported: list[str]
                    - inferenceTypesSupported: list[str]

        Example:
            >>> client = BedrockRuntime(region_name='us-east-1')
            >>> response = client.list_foundation_models()
            >>> for model in response['modelSummaries']:
            ...     print(f"{model['modelId']} - {model['providerName']}")
        """
        # Run async version in sync context
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(
                self._list_foundation_models_async(
                    byProvider=byProvider,
                    byCustomizationType=byCustomizationType,
                    byOutputModality=byOutputModality,
                    byInferenceType=byInferenceType,
                )
            )
        finally:
            loop.close()

    async def _list_foundation_models_async(
        self,
        byProvider: str | None = None,  # noqa: N803
        byCustomizationType: str | None = None,  # noqa: N803
        byOutputModality: str | None = None,  # noqa: N803
        byInferenceType: str | None = None,  # noqa: N803
    ) -> dict[str, Any]:
        """Async implementation of list_foundation_models."""
        # For Bedrock models: use raw adapter to get native boto3 response
        try:
            bedrock_adapter = get_adapter("bedrock", credentials=self._bedrock_credentials)
            raw_response = await bedrock_adapter.list_models_raw()  # type: ignore[attr-defined]

            # If Cerebras credentials available, add Cerebras models to the response
            if self._cerebras_credentials:
                try:
                    cerebras_adapter = get_adapter(
                        "cerebras", credentials=self._cerebras_credentials
                    )
                    cerebras_raw = await cerebras_adapter.list_models_raw()  # type: ignore[attr-defined]

                    # Use CerebrasToBedrockMapper to convert to Bedrock format
                    cerebras_bedrock_response = CerebrasToBedrockMapper.map_model_list(cerebras_raw)
                    cerebras_models = cerebras_bedrock_response.get("modelSummaries", [])

                    # Merge Cerebras models with Bedrock models
                    model_summaries = raw_response.get("modelSummaries", [])
                    model_summaries.extend(cerebras_models)
                    raw_response["modelSummaries"] = model_summaries
                except Exception:  # noqa: S110
                    pass  # Cerebras might not be configured

            # Apply filters if provided
            if byProvider:
                filtered_summaries = [
                    s
                    for s in raw_response.get("modelSummaries", [])
                    if s.get("providerName", "").lower() == byProvider.lower()
                ]
                raw_response["modelSummaries"] = filtered_summaries

            return raw_response  # type: ignore[no-any-return]

        except Exception:  # noqa: BLE001
            # Fallback to empty list
            return {"modelSummaries": []}

    def converse(
        self,
        modelId: str,  # noqa: N803 - Bedrock uses this casing
        messages: list[dict[str, Any]],
        inferenceConfig: dict[str, Any] | None = None,  # noqa: N803
        additionalModelRequestFields: dict[str, Any] | None = None,  # noqa: N803
        **kwargs: Any,
    ) -> BedrockConverseResponse:
        """Bedrock Converse API compatible method.

        This method accepts Bedrock-format requests and returns Bedrock-format responses,
        while internally routing to the appropriate provider (Bedrock or Cerebras).

        Args:
            modelId: Model identifier. Can be AWS Bedrock model or Cerebras model.
                Examples: "anthropic.claude-3-haiku-20240307-v1:0", "cerebras.llama3.1-8b"
            messages: Bedrock-format messages. Each message has:
                - role: "user" or "assistant"
                - content: List of dicts with "text" key
            inferenceConfig: Optional inference configuration with:
                - temperature: float (0.0-1.0)
                - maxTokens: int
                - topP: float
                - stopSequences: list[str]
            additionalModelRequestFields: Optional provider-specific fields.
            **kwargs: Additional parameters.

        Returns:
            BedrockConverseResponse: Typed response matching boto3 bedrock-runtime structure:
                - output.message.role: "assistant"
                - output.message.content: List of content blocks with "text"
                - stopReason: "end_turn" | "max_tokens" | "stop_sequence"
                - usage: inputTokens, outputTokens, totalTokens
                - metrics: latencyMs

        Example:
            >>> response = client.converse(
            ...     modelId='cerebras.llama3.1-8b',
            ...     messages=[
            ...         {
            ...             "role": "user",
            ...             "content": [{"text": "What is 2+2?"}]
            ...         }
            ...     ],
            ...     inferenceConfig={
            ...         "temperature": 0.7,
            ...         "maxTokens": 100
            ...     }
            ... )
            >>> print(response['output']['message']['content'][0]['text'])
        """
        # Run async version in sync context
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(
                self._converse_async(
                    modelId=modelId,
                    messages=messages,
                    inferenceConfig=inferenceConfig,
                    additionalModelRequestFields=additionalModelRequestFields,
                    **kwargs,
                )
            )
        finally:
            loop.close()

    async def _converse_async(
        self,
        modelId: str,  # noqa: N803
        messages: list[dict[str, Any]],
        inferenceConfig: dict[str, Any] | None = None,  # noqa: N803
        additionalModelRequestFields: dict[str, Any] | None = None,  # noqa: N803
        **kwargs: Any,
    ) -> BedrockConverseResponse:
        """Async implementation of converse."""
        # Detect provider from model ID
        provider = self._detect_provider(modelId)

        # Get appropriate adapter
        credentials = (
            self._cerebras_credentials if provider == "cerebras" else self._bedrock_credentials
        )
        adapter = get_adapter(provider, credentials=credentials)

        # Convert Bedrock messages to OpenAI format
        openai_messages = self._convert_messages_to_openai(messages)

        # Extract inference config
        config = inferenceConfig or {}

        # Normalize model ID (remove provider prefix)
        normalized_model = self._normalize_model_id(modelId)

        # Convert message dicts to Message objects
        message_objs = [Message(role=m["role"], content=m["content"]) for m in openai_messages]

        # Build request (only include supported ChatRequest fields)
        request = ChatRequest(
            provider=provider,
            model=normalized_model,
            messages=message_objs,
            temperature=config.get("temperature", 0.7),
            max_tokens=config.get("maxTokens", 100),
        )

        # For Bedrock: use raw method to get native boto3 response
        # For Cerebras: use mapper to convert to Bedrock format
        if provider == "bedrock":
            # Get native Bedrock response for strict backward compatibility
            raw_response = await adapter.invoke_raw(request)  # type: ignore[attr-defined]
            return raw_response  # type: ignore[no-any-return]
        else:
            # Cerebras: get native response, then convert to Bedrock format
            cerebras_raw = await adapter.invoke_raw(request)  # type: ignore[attr-defined]

            # Convert Cerebras response to dict for mapper
            if hasattr(cerebras_raw, "model_dump"):
                cerebras_dict = cerebras_raw.model_dump()
            else:
                cerebras_dict = dict(cerebras_raw)

            # Use CerebrasToBedrockMapper to convert directly to Bedrock format
            bedrock_response = CerebrasToBedrockMapper.map_chat_completion(cerebras_dict)
            return bedrock_response  # type: ignore[return-value]

    def _detect_provider(self, model_id: str) -> str:
        """Detect provider from model ID.

        Args:
            model_id: Model identifier.

        Returns:
            Provider name ("cerebras" or "bedrock").
        """
        model_lower = model_id.lower()

        # Cerebras patterns
        if model_lower.startswith("cerebras.") or model_lower.startswith("cerebras/"):
            return "cerebras"

        # Default to bedrock for AWS model IDs
        return "bedrock"

    def _normalize_model_id(self, model_id: str) -> str:
        """Normalize model ID by removing provider prefix.

        Args:
            model_id: Original model ID.

        Returns:
            Normalized model ID without provider prefix.
        """
        # Remove "cerebras." or "cerebras/" prefix
        if model_id.startswith("cerebras."):
            return model_id[9:]  # len("cerebras.") = 9
        if model_id.startswith("cerebras/"):
            return model_id[9:]  # len("cerebras/") = 9

        # Bedrock models use full ID
        return model_id

    def _convert_messages_to_openai(
        self, bedrock_messages: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Convert Bedrock message format to OpenAI format.

        Handles two input formats:
        1. Standard Bedrock format: [{"role": "user", "content": [{"text": "Hello"}]}]
        2. Simplified format: [{"role": "user", "content": "Hello"}]

        OpenAI output format:
            [{"role": "user", "content": "Hello"}]

        Args:
            bedrock_messages: List of Bedrock-format messages.

        Returns:
            List of OpenAI-format messages.
        """
        openai_messages = []

        for msg in bedrock_messages:
            role = msg["role"]
            content_raw = msg.get("content", "")

            # Handle both list (Bedrock) and string (simplified) formats
            if isinstance(content_raw, str):
                # Already in string format
                content = content_raw
            elif isinstance(content_raw, list):
                # Extract text from content list
                text_parts = []
                for content_item in content_raw:
                    if isinstance(content_item, dict) and "text" in content_item:
                        text_parts.append(content_item["text"])
                    elif isinstance(content_item, str):
                        text_parts.append(content_item)

                # Combine all text parts
                content = " ".join(text_parts) if text_parts else ""
            else:
                content = str(content_raw)

            # Only add message if content is non-empty
            if content:
                openai_messages.append({"role": role, "content": content})

        return openai_messages

    def _convert_response_to_bedrock(
        self, unified_response: UnifiedChatResponse, start_time: float
    ) -> BedrockConverseResponse:
        """Convert UnifiedChatResponse to Bedrock format.

        Args:
            unified_response: UnifiedAI response object.
            start_time: Request start time for latency calculation.

        Returns:
            Bedrock-format response dictionary.
        """
        # Extract message content (message is dict[str, str])
        message_content = unified_response.choices[0].message.get("content", "")

        # Map finish reason to Bedrock stop reason
        finish_reason = unified_response.choices[0].finish_reason or "end_turn"
        stop_reason_map = {
            "stop": "end_turn",
            "length": "max_tokens",
            "content_filter": "content_filtered",
        }
        stop_reason = stop_reason_map.get(finish_reason, finish_reason)

        # Calculate latency (ensure it's always a float)
        latency_ms: float = (
            unified_response.metrics.duration_ms
            if unified_response.metrics and unified_response.metrics.duration_ms is not None
            else ((time.perf_counter() - start_time) * 1000)
        )

        # Build Bedrock response
        return BedrockConverseResponse(
            output=BedrockOutput(
                message=BedrockMessage(
                    role="assistant",
                    content=[BedrockContentBlock(text=message_content)],
                )
            ),
            stopReason=stop_reason,
            usage=BedrockUsage(
                inputTokens=unified_response.usage.prompt_tokens,
                outputTokens=unified_response.usage.completion_tokens,
                totalTokens=unified_response.usage.total_tokens,
            ),
            metrics=BedrockMetrics(latencyMs=latency_ms),
        )
