"""Response models normalized to OpenAI-compatible schema."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Choice(BaseModel):
    model_config = ConfigDict(strict=True)
    index: int
    message: dict[str, str]
    finish_reason: str | None = None


class Usage(BaseModel):
    model_config = ConfigDict(strict=True)
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ProviderMetadata(BaseModel):
    model_config = ConfigDict(strict=True)
    provider: str
    raw: dict[str, object] | None = None


class ResponseMetrics(BaseModel):
    """Performance metrics for a chat completion request.

    This model contains ONLY metrics that are either:
    1. Measured by the SDK (duration_ms)
    2. Provided directly by the provider (all other fields)

    We do NOT calculate or estimate any provider-side metrics. If a provider
    doesn't provide a metric, it will be null.

    Attributes:
        duration_ms: SDK-measured total time from request start to response received.
            Includes network latency, SDK overhead, and provider processing time.
            This is the ONLY metric calculated by the SDK.

        Provider-specific metrics (null if not provided by that provider):

        provider_time_info: Raw timing information from the provider (dict).
            Contains whatever timing fields the provider sends.
            - Cerebras: queue_time, prompt_time, completion_time, total_time, created
            - Bedrock: Currently none provided
            - Structure varies by provider - see provider_metadata.raw for details

    Example from Cerebras:
        duration_ms: 2824.47  # SDK measured
        provider_time_info: {
            "queue_time": 212.5,      # Cerebras-provided
            "prompt_time": 0.7,       # Cerebras-provided
            "completion_time": 2254,  # Cerebras-provided
            "total_time": 2467,       # Cerebras-provided
            "created": 1729089471     # Cerebras-provided
        }

    Example from Bedrock:
        duration_ms: 1523.89  # SDK measured
        provider_time_info: None  # Bedrock doesn't provide timing info

    Note: All provider-specific timing details are also available in
    provider_metadata.raw for full transparency.
    """

    model_config = ConfigDict(strict=True)

    # SDK-measured metric (always present)
    duration_ms: float

    # Provider-supplied metrics (null if provider doesn't provide them)
    provider_time_info: dict[str, float | int] | None = None


class UnifiedChatResponse(BaseModel):
    model_config = ConfigDict(strict=True)

    id: str
    object: Literal["chat.completion"]
    created: int
    model: str
    choices: list[Choice]
    usage: Usage = Field(default_factory=Usage)
    provider_metadata: ProviderMetadata | None = None
    metrics: ResponseMetrics | None = None
