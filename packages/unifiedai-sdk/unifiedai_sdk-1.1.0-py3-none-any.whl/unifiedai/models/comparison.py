"""Comparison result models for side-by-side provider execution."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from .request import ChatRequest
from .response import UnifiedChatResponse


class ProviderResult(BaseModel):
    """Result from a single provider in a comparison.

    Attributes:
        provider: Provider identifier (e.g., "cerebras", "bedrock")
        model: Model identifier used for this provider
        success: Whether the provider call succeeded
        response: Full response from provider (includes metrics). None if failed.
        error: Error message if call failed. None if succeeded.

    Note:
        Metrics are available in response.metrics when success=True.
        For failed calls, use the error field for details.
    """

    model_config = ConfigDict(strict=True)

    provider: str
    model: str
    success: bool
    response: UnifiedChatResponse | None = None
    error: str | None = None


class ComparativeMetrics(BaseModel):
    model_config = ConfigDict(strict=True)

    speed_difference_ms: float = 0.0
    token_efficiency: dict[str, float] = Field(default_factory=dict)
    cost_difference: float | None = None
    quality_score: float | None = None


class ComparisonResult(BaseModel):
    model_config = ConfigDict(strict=True)

    correlation_id: str
    timestamp: datetime
    request: ChatRequest
    provider_a: ProviderResult
    provider_b: ProviderResult
    comparative_metrics: ComparativeMetrics = Field(default_factory=ComparativeMetrics)
    winner: str | None = None  # "provider_a", "provider_b", or "tie"
