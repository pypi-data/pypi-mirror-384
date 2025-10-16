"""Comparison mode orchestration.

Implements side-by-side provider invocation with fairness constraints and
observability. Both providers receive identically preprocessed messages, are
invoked in parallel with per-provider and overall timeouts enforced, and
metrics/traces are emitted for each call.

Returned value is a ``ComparisonResult`` containing per-provider outcomes and a
computed winner signal based on response time (extensible for quality/cost).
"""

from __future__ import annotations

import asyncio
import time
from datetime import datetime, timezone
from typing import Literal

from opentelemetry import trace

from .._context import RequestContext
from .._exceptions import ComparisonError
from .._logging import logger
from ..adapters.registry import get_adapter
from ..metrics.emitter import (
    active_requests,
    request_duration_seconds,
    requests_total,
    ttfb_seconds,
)
from ..models.comparison import ComparativeMetrics, ComparisonResult, ProviderResult
from ..models.config import TimeoutConfig
from ..models.request import ChatRequest, Message
from ..models.response import UnifiedChatResponse

tracer = trace.get_tracer(__name__)


def preprocess_messages(messages: list[dict[str, object]]) -> list[dict[str, str]]:
    """Normalize incoming message dicts into a safe, trimmed format.

    Ensures roles are strings and content is stripped of surrounding whitespace.
    """
    return [
        {
            "role": str(m.get("role", "user")),
            "content": str(m.get("content", "")).strip(),
        }
        for m in messages
    ]


def normalize_role(value: str) -> Literal["system", "user", "assistant"]:
    """Coerce free-form role strings into one of the allowed values."""
    v = value.lower()
    if v == "system":
        return "system"
    if v == "assistant":
        return "assistant"
    return "user"


async def _invoke_with_timeout(
    provider: str,
    request: ChatRequest,
    provider_timeout: float,
    credentials: dict[str, str] | None = None,
) -> tuple[str, UnifiedChatResponse | Exception, float, float]:
    """Invoke a single provider with metrics tracking.

    Note: Retry, circuit breaker, and timeout are now handled by BaseAdapter.invoke_with_limit().
    This function just tracks metrics and handles exceptions.

    Returns a tuple of (provider, result_or_exception, duration_seconds, ttfb_seconds).
    """
    adapter = get_adapter(provider, credentials=credentials)
    active_requests.labels(provider=provider).inc()
    start = time.perf_counter()
    ttfb = None
    try:
        with tracer.start_as_current_span(
            "provider.invoke", attributes={"provider": provider, "model": request.model}
        ):
            # BaseAdapter.invoke_with_limit() now handles:
            # - Concurrency limiting (semaphore)
            # - Circuit breaker (fail fast if provider is down)
            # - Retry with exponential backoff (for transient errors)
            # - Timeout enforcement (per-request timeout)
            result = await adapter.invoke_with_limit(request)
            duration = time.perf_counter() - start
            ttfb = duration
            requests_total.labels(provider=provider, model=request.model, status="success").inc()
            request_duration_seconds.labels(provider=provider, model=request.model).observe(
                duration
            )
            ttfb_seconds.labels(provider=provider, model=request.model).observe(ttfb)
            return provider, result, duration, ttfb
    except Exception as exc:  # noqa: BLE001
        duration = time.perf_counter() - start
        requests_total.labels(provider=provider, model=request.model, status="error").inc()
        logger.error(
            "provider_invocation_failed",
            provider=provider,
            model=request.model,
            error=type(exc).__name__,
            error_message=str(exc),
            duration_ms=duration * 1000.0,
            exc_info=True,  # Include full stack trace in logs
        )
        return provider, exc, duration, ttfb or duration
    finally:
        active_requests.labels(provider=provider).dec()


async def compare_async(
    *,
    providers: list[str],
    model: str | None = None,
    models: dict[str, str] | None = None,
    messages: list[dict[str, object]],
    timeouts: TimeoutConfig | None = None,
    credentials_by_provider: dict[str, dict[str, str]] | None = None,
) -> ComparisonResult:
    """Run a side-by-side comparison of two providers in parallel.

    Enforces fairness (identical inputs), per-provider timeouts, overall
    comparison timeout, and collects metrics and tracing data.

    Args:
        providers: Exactly two provider identifiers (e.g., ["cerebras", "bedrock"]).
        model: Model identifier shared across both providers. Mutually exclusive with
            ``models``.
        models: Dict mapping provider names to their specific model IDs. Mutually exclusive
            with ``model``. Example: ``{"cerebras": "llama3.1-8b", "bedrock":
            "meta.llama3-1-8b-instruct-v1:0"}``
        messages: Conversation messages (list of dicts with role/content).
        timeouts: Optional timeout configuration.
        credentials_by_provider: Optional dict mapping provider names to their credentials.

    Returns:
        ComparisonResult: Per-provider outcomes and comparative metrics.

    Raises:
        ValueError: If exactly two providers are not specified, or if both/neither
            ``model`` and ``models`` are provided, or if ``models`` is missing entries.
    """
    if len(providers) != 2:
        raise ValueError("Exactly two providers must be specified for comparison")

    # Validate model/models parameter usage
    if model is not None and models is not None:
        raise ValueError("Specify either 'model' (shared) or 'models' (per-provider), not both")
    if model is None and models is None:
        raise ValueError("Must specify either 'model' (shared) or 'models' (per-provider)")

    # Build per-provider model mapping
    if model is not None:
        # Shared model: use same ID for both providers
        model_map = {providers[0]: model, providers[1]: model}
    else:
        # Per-provider models: validate all providers are present
        assert models is not None
        for provider in providers:
            if provider not in models:
                raise ValueError(
                    f"Provider '{provider}' missing from models dict. "
                    f"Expected keys: {providers}, got: {list(models.keys())}"
                )
        model_map = models

    timeouts = timeouts or TimeoutConfig(
        connect_timeout=5.0,
        read_timeout=30.0,
        provider_timeout=60.0,
        sdk_timeout=90.0,
        comparison_timeout=120.0,
    )
    assert timeouts.comparison_timeout > timeouts.provider_timeout

    normalized_messages = preprocess_messages(messages)
    ctx = RequestContext.new()

    # Create normalized message list (shared across both providers)
    normalized_message_list = [
        Message(
            role=normalize_role(m["role"]),
            content=m["content"],
        )
        for m in normalized_messages
    ]

    provider_timeout = timeouts.provider_timeout
    credentials_map = credentials_by_provider or {}

    with tracer.start_as_current_span("comparison.compare"):
        tasks: list[asyncio.Task[tuple[str, UnifiedChatResponse | Exception, float, float]]] = [
            asyncio.create_task(
                _invoke_with_timeout(
                    providers[0],
                    ChatRequest(
                        provider=providers[0],
                        model=model_map[providers[0]],
                        messages=normalized_message_list,
                        temperature=0.7,
                        max_tokens=256,
                    ),
                    provider_timeout,
                    credentials=credentials_map.get(providers[0]),
                )
            ),
            asyncio.create_task(
                _invoke_with_timeout(
                    providers[1],
                    ChatRequest(
                        provider=providers[1],
                        model=model_map[providers[1]],
                        messages=normalized_message_list,
                        temperature=0.7,
                        max_tokens=256,
                    ),
                    provider_timeout,
                    credentials=credentials_map.get(providers[1]),
                )
            ),
        ]
        try:
            done = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=False), timeout=timeouts.comparison_timeout
            )
        except asyncio.TimeoutError:
            results: list[tuple[str, UnifiedChatResponse | Exception, float, float]] = []
            done_tasks = [t for t in tasks if t.done()]
            for t in done_tasks:
                results.append(t.result())
            while len(results) < 2:
                results.append(("unknown", ComparisonError("timeout"), 0.0, 0.0))
            a_provider, a_result, a_duration, a_ttfb = results[0]
            b_provider, b_result, b_duration, b_ttfb = results[1]
        else:
            a_provider, a_result, a_duration, a_ttfb = done[0]
            b_provider, b_result, b_duration, b_ttfb = done[1]

    def to_provider_result(
        provider: str, value: UnifiedChatResponse | Exception, duration: float, ttfb: float
    ) -> ProviderResult:
        if isinstance(value, UnifiedChatResponse):
            # Success: metrics are already in value.metrics
            return ProviderResult(
                provider=provider,
                model=model_map[provider],
                success=True,
                response=value,  # Already contains full metrics in value.metrics
                error=None,
            )
        # Failure: include detailed error message
        error_type = type(value).__name__
        error_message = str(value)
        full_error = f"{error_type}: {error_message}" if error_message else error_type
        return ProviderResult(
            provider=provider,
            model=model_map[provider],
            success=False,
            response=None,
            error=full_error,
        )

    provider_a = to_provider_result(a_provider, a_result, a_duration, a_ttfb)
    provider_b = to_provider_result(b_provider, b_result, b_duration, b_ttfb)

    # Calculate speed difference from response metrics (if both succeeded)
    duration_a = (
        provider_a.response.metrics.duration_ms
        if provider_a.response and provider_a.response.metrics
        else a_duration * 1000.0
    )
    duration_b = (
        provider_b.response.metrics.duration_ms
        if provider_b.response and provider_b.response.metrics
        else b_duration * 1000.0
    )
    speed_diff = (duration_b or 0.0) - (duration_a or 0.0)

    # Build a representative request for the comparison result
    # Use first provider's model for the request field (both models are equivalent)
    comparison_request = ChatRequest(
        provider="comparison",
        model=model_map[providers[0]],
        messages=normalized_message_list,
        temperature=0.7,
        max_tokens=256,
    )

    return ComparisonResult(
        correlation_id=ctx.correlation_id,
        timestamp=datetime.now(timezone.utc),
        request=comparison_request,
        provider_a=provider_a,
        provider_b=provider_b,
        comparative_metrics=ComparativeMetrics(speed_difference_ms=speed_diff),
        winner=("provider_a" if speed_diff > 0 else ("provider_b" if speed_diff < 0 else "tie")),
    )
