"""Response mappers for converting provider-specific responses to UnifiedChatResponse.

This module contains mapper functions that transform native provider responses
into our unified OpenAI-compatible format. This separation allows:
1. Clean backward compatibility (raw responses for compat layer)
2. Unified interface (mapped responses for cross-provider use)
"""

from __future__ import annotations

from typing import Any

from ..models.response import (
    Choice,
    ProviderMetadata,
    ResponseMetrics,
    UnifiedChatResponse,
    Usage,
)


class ResponseMapper:
    """Base mapper with common utilities."""

    @staticmethod
    def create_fallback_id(provider: str) -> str:
        """Generate a fallback ID if provider doesn't provide one."""
        import uuid

        return f"{provider}-{uuid.uuid4()}"


class CerebrasResponseMapper(ResponseMapper):
    """Mapper for Cerebras responses to UnifiedChatResponse."""

    @staticmethod
    def map_to_unified(
        raw: dict[str, Any],
        *,
        duration_ms: float,
        started_epoch: int,
        model: str,
        extract_reasoning: bool = True,
    ) -> UnifiedChatResponse:
        """Map Cerebras response to UnifiedChatResponse.

        Args:
            raw: Raw response dict from Cerebras SDK
            duration_ms: SDK-measured duration in milliseconds
            started_epoch: Request start timestamp
            model: Model identifier
            extract_reasoning: Whether to extract <think> tags

        Returns:
            UnifiedChatResponse with metrics and provider metadata
        """
        # Extract reasoning if enabled
        reasoning = None
        content = CerebrasResponseMapper._get_content(raw)

        if extract_reasoning and content:
            reasoning, content = CerebrasResponseMapper._extract_reasoning(content)

        # Build choices
        choices_raw = raw.get("choices") or []
        first = choices_raw[0] if choices_raw else {}
        message = first.get("message") or {"role": "assistant", "content": content}

        choices = [
            Choice(
                index=int(first.get("index") or 0),
                message={
                    "role": str(message.get("role") or "assistant"),
                    "content": content or "",
                },
                finish_reason=first.get("finish_reason"),
            )
        ]

        # Build usage
        usage_raw = raw.get("usage") or {}
        usage = Usage(
            prompt_tokens=int(usage_raw.get("prompt_tokens") or 0),
            completion_tokens=int(usage_raw.get("completion_tokens") or 0),
            total_tokens=int(usage_raw.get("total_tokens") or 0),
        )

        # Extract provider timing info
        time_info = raw.get("time_info")
        provider_time_info: dict[str, float | int] | None = None

        if time_info and isinstance(time_info, dict):
            provider_time_info = {}
            for key, value in time_info.items():
                if not isinstance(key, str):
                    continue
                try:
                    if value is not None:  # Skip None values
                        num_val = float(value)
                        provider_time_info[key] = int(num_val) if num_val.is_integer() else num_val
                except (ValueError, TypeError):
                    pass

        # Build metrics
        metrics = ResponseMetrics(
            duration_ms=duration_ms,
            provider_time_info=provider_time_info,
        )

        # Build provider metadata
        meta_raw = dict(raw)
        if reasoning:
            meta_raw["reasoning"] = reasoning

        provider_metadata = ProviderMetadata(provider="cerebras", raw=meta_raw)

        # Build response
        return UnifiedChatResponse(
            id=str(raw.get("id") or CerebrasResponseMapper.create_fallback_id("cerebras")),
            object="chat.completion",
            created=int(raw.get("created") or started_epoch),
            model=str(raw.get("model") or model),
            choices=choices,
            usage=usage,
            provider_metadata=provider_metadata,
            metrics=metrics,
        )

    @staticmethod
    def _get_content(raw: dict[str, Any]) -> str:
        """Extract content from raw response."""
        try:
            choices = raw.get("choices") or []
            if choices:
                first = choices[0]
                msg = first.get("message") or {}
                return str(msg.get("content") or first.get("text") or "")
        except Exception:  # noqa: BLE001
            pass
        return ""

    @staticmethod
    def _extract_reasoning(content: str) -> tuple[str | None, str]:
        """Extract <think>...</think> tags as reasoning.

        Returns:
            Tuple of (reasoning, cleaned_content)
        """
        import re

        if not isinstance(content, str):
            content = str(content)

        match = re.search(r"<think>(.*?)</think>", content, flags=re.DOTALL | re.IGNORECASE)
        reasoning = match.group(1).strip() if match else None
        cleaned = re.sub(
            r"<think>.*?</think>", "", content, flags=re.DOTALL | re.IGNORECASE
        ).strip()

        return reasoning, cleaned


class BedrockToCerebrasMapper:
    """Mapper to convert Bedrock responses to Cerebras SDK format.

    Used when Bedrock models are called through Cerebras compatibility layer.
    Converts native boto3 Bedrock responses to Cerebras SDK format.
    """

    @staticmethod
    def map_chat_completion(bedrock_response: dict[str, Any]) -> dict[str, Any]:
        """Convert Bedrock Converse response to Cerebras ChatCompletion format.

        Args:
            bedrock_response: Native boto3 Bedrock Converse response dict

        Returns:
            Dict in Cerebras SDK ChatCompletion format
        """
        import time
        import uuid

        # Extract content from Bedrock format
        output = bedrock_response.get("output", {})
        message = output.get("message", {})
        content_blocks = message.get("content", [])

        # Combine all text blocks
        content = " ".join(
            block.get("text", "")
            for block in content_blocks
            if isinstance(block, dict) and "text" in block
        )

        # Extract usage
        usage = bedrock_response.get("usage", {})

        # Map stop reason
        stop_reason = bedrock_response.get("stopReason", "stop")
        finish_reason_map = {
            "end_turn": "stop",
            "max_tokens": "length",
            "content_filtered": "content_filter",
        }
        finish_reason = finish_reason_map.get(stop_reason, stop_reason)

        # Build Cerebras format response
        return {
            "id": f"chatcmpl-{uuid.uuid4()}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": "bedrock-proxied",  # Indicate this came through Bedrock
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": content,
                    },
                    "finish_reason": finish_reason,
                }
            ],
            "usage": {
                "prompt_tokens": usage.get("inputTokens", 0),
                "completion_tokens": usage.get("outputTokens", 0),
                "total_tokens": usage.get("totalTokens", 0),
            },
            # Include Bedrock-specific timing if available
            "time_info": bedrock_response.get("metrics", {}),
        }

    @staticmethod
    def map_model_list(bedrock_response: dict[str, Any]) -> list[dict[str, Any]]:
        """Convert Bedrock list_foundation_models response to Cerebras model list format.

        Args:
            bedrock_response: Native boto3 list_foundation_models response

        Returns:
            List of model dicts in Cerebras SDK format
        """
        models = []
        for summary in bedrock_response.get("modelSummaries", []):
            models.append(
                {
                    "id": summary.get("modelId", ""),
                    "object": "model",
                    "created": 1704067200,  # Bedrock GA date
                    "owned_by": summary.get("providerName", "aws").lower(),
                }
            )
        return models


class CerebrasToBedrockMapper:
    """Mapper to convert Cerebras responses to Bedrock SDK format.

    Used when Cerebras models are called through Bedrock compatibility layer.
    Converts native Cerebras SDK responses to boto3 Bedrock format.
    """

    @staticmethod
    def map_chat_completion(cerebras_response: dict[str, Any]) -> dict[str, Any]:
        """Convert Cerebras ChatCompletion to Bedrock Converse response format.

        Args:
            cerebras_response: Native Cerebras SDK ChatCompletion dict

        Returns:
            Dict in boto3 Bedrock Converse API format
        """
        # Extract content from Cerebras format
        choices = cerebras_response.get("choices", [])
        if choices:
            first_choice = choices[0]
            message = first_choice.get("message", {})
            content = message.get("content", "")
            finish_reason = first_choice.get("finish_reason", "stop")
        else:
            content = ""
            finish_reason = "stop"

        # Map finish reason to Bedrock stop reason
        finish_reason_map = {
            "stop": "end_turn",
            "length": "max_tokens",
            "content_filter": "content_filtered",
        }
        stop_reason = finish_reason_map.get(finish_reason, "end_turn")

        # Extract usage
        usage = cerebras_response.get("usage", {})

        # Build Bedrock format response
        return {
            "output": {
                "message": {
                    "role": "assistant",
                    "content": [{"text": content}],
                }
            },
            "stopReason": stop_reason,
            "usage": {
                "inputTokens": usage.get("prompt_tokens", 0),
                "outputTokens": usage.get("completion_tokens", 0),
                "totalTokens": usage.get("total_tokens", 0),
            },
            "metrics": cerebras_response.get("time_info", {}),
        }

    @staticmethod
    def map_model_list(cerebras_response: Any) -> dict[str, Any]:
        """Convert Cerebras ModelListResponse to Bedrock list_foundation_models format.

        Args:
            cerebras_response: Cerebras SDK ModelListResponse object

        Returns:
            Dict in boto3 list_foundation_models format
        """
        model_summaries = []

        # Extract models from Cerebras response
        if hasattr(cerebras_response, "data"):
            models_data = cerebras_response.data
        else:
            models_data = []

        for model in models_data:
            model_dict = model.model_dump() if hasattr(model, "model_dump") else dict(model)
            model_summaries.append(
                {
                    "modelId": f"cerebras.{model_dict.get('id', '')}",
                    "modelArn": "N/A",  # noqa: E501
                    "modelName": model_dict.get("id", ""),
                    "providerName": "Cerebras",
                    "inputModalities": ["TEXT"],
                    "outputModalities": ["TEXT"],
                    "responseStreamingSupported": True,
                    "customizationsSupported": [],
                    "inferenceTypesSupported": ["ON_DEMAND"],
                }
            )

        return {"modelSummaries": model_summaries}


class BedrockResponseMapper(ResponseMapper):
    """Mapper for AWS Bedrock responses to UnifiedChatResponse."""

    @staticmethod
    def map_to_unified(
        raw: dict[str, Any],
        *,
        duration_ms: float,
        started_epoch: int,
        model: str,
    ) -> UnifiedChatResponse:
        """Map Bedrock Converse response to UnifiedChatResponse.

        Args:
            raw: Raw response dict from Bedrock Converse API
            duration_ms: SDK-measured duration in milliseconds
            started_epoch: Request start timestamp
            model: Model identifier

        Returns:
            UnifiedChatResponse with metrics and provider metadata
        """
        # Extract content from Bedrock format
        output = raw.get("output") or {}
        message = output.get("message") or {}
        content_blocks = message.get("content") or []

        # Combine all text blocks
        content = " ".join(
            block.get("text", "")
            for block in content_blocks
            if isinstance(block, dict) and "text" in block
        )

        # Build choices
        choices = [
            Choice(
                index=0,
                message={
                    "role": str(message.get("role") or "assistant"),
                    "content": content,
                },
                finish_reason=raw.get("stopReason"),
            )
        ]

        # Build usage
        usage_raw = raw.get("usage") or {}
        usage = Usage(
            prompt_tokens=int(usage_raw.get("inputTokens") or 0),
            completion_tokens=int(usage_raw.get("outputTokens") or 0),
            total_tokens=int(usage_raw.get("totalTokens") or 0),
        )

        # Extract provider timing info (if any)
        metrics_data = raw.get("metrics")
        provider_time_info: dict[str, float | int] | None = None

        if metrics_data and isinstance(metrics_data, dict):
            provider_time_info = {}
            for key, value in metrics_data.items():
                if not isinstance(key, str):
                    continue
                try:
                    if value is not None:  # Skip None values
                        num_val = float(value)
                        provider_time_info[key] = int(num_val) if num_val.is_integer() else num_val
                except (ValueError, TypeError):
                    pass

        # Build metrics
        metrics = ResponseMetrics(
            duration_ms=duration_ms,
            provider_time_info=provider_time_info,
        )

        # Build provider metadata
        provider_metadata = ProviderMetadata(provider="bedrock", raw=dict(raw))

        # Build response
        response_id = raw.get("ResponseMetadata", {}).get(
            "RequestId"
        ) or BedrockResponseMapper.create_fallback_id("bedrock")
        return UnifiedChatResponse(
            id=str(response_id),
            object="chat.completion",
            created=started_epoch,
            model=model,
            choices=choices,
            usage=usage,
            provider_metadata=provider_metadata,
            metrics=metrics,
        )
