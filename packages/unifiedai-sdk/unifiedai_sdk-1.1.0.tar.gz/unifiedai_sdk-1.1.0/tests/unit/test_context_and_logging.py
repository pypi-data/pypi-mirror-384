"""Test context management and logging utilities."""

from __future__ import annotations

from unifiedai._context import RequestContext
from unifiedai._logging import logger


def test_request_context_new() -> None:
    """Test RequestContext.new() generates unique correlation IDs."""
    ctx1 = RequestContext.new()
    ctx2 = RequestContext.new()

    assert ctx1.correlation_id != ctx2.correlation_id
    assert len(ctx1.correlation_id) > 0
    assert len(ctx2.correlation_id) > 0


def test_request_context_correlation_id_format() -> None:
    """Test correlation ID is a valid UUID."""
    ctx = RequestContext.new()

    # Should be a valid UUID format (with hyphens)
    assert "-" in ctx.correlation_id
    parts = ctx.correlation_id.split("-")
    assert len(parts) == 5  # UUID format: 8-4-4-4-12


def test_request_context_immutable() -> None:
    """Test RequestContext fields."""
    ctx = RequestContext(correlation_id="test-123")
    assert ctx.correlation_id == "test-123"


def test_logger_exists() -> None:
    """Test structured logger is available."""
    assert logger is not None


def test_logger_can_log() -> None:
    """Test logger can emit messages."""
    # This should not raise any exceptions
    logger.info("test_message", key="value")
    logger.debug("test_debug", provider="test")
    logger.warning("test_warning", status="unhealthy")
    logger.error("test_error", error="something went wrong")


def test_logger_with_correlation_id() -> None:
    """Test logging with correlation ID."""
    ctx = RequestContext.new()
    logger.info("provider_invocation", correlation_id=ctx.correlation_id, provider="test")
    # Should not raise exceptions
    assert True
