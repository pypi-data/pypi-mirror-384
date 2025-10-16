"""Test health check functionality."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from unifiedai._health import ProviderHealth, health_check


@pytest.mark.asyncio
async def test_health_check_all_healthy() -> None:
    """Test health check when all providers are healthy."""
    # Mock get_adapter to return mock adapters
    mock_cerebras = AsyncMock()
    mock_cerebras.health_check = AsyncMock(
        return_value={"status": "healthy", "provider": "cerebras"}
    )

    mock_bedrock = AsyncMock()
    mock_bedrock.health_check = AsyncMock(return_value={"status": "healthy", "provider": "bedrock"})

    def mock_get_adapter(provider: str):  # type: ignore[no-untyped-def]
        if provider == "cerebras":
            return mock_cerebras
        return mock_bedrock

    with patch("unifiedai._health.get_adapter", side_effect=mock_get_adapter):
        result = await health_check(["cerebras", "bedrock"])

        assert result.status == "healthy"
        assert len(result.providers) == 2
        assert result.providers["cerebras"].status == "healthy"
        assert result.providers["bedrock"].status == "healthy"


@pytest.mark.asyncio
async def test_health_check_one_unhealthy() -> None:
    """Test health check when one provider is unhealthy."""
    mock_cerebras = AsyncMock()
    mock_cerebras.health_check = AsyncMock(
        return_value={"status": "healthy", "provider": "cerebras"}
    )

    mock_bedrock = AsyncMock()
    mock_bedrock.health_check = AsyncMock(
        return_value={"status": "unhealthy", "provider": "bedrock"}
    )

    def mock_get_adapter(provider: str):  # type: ignore[no-untyped-def]
        if provider == "cerebras":
            return mock_cerebras
        return mock_bedrock

    with patch("unifiedai._health.get_adapter", side_effect=mock_get_adapter):
        result = await health_check(["cerebras", "bedrock"])

        assert result.status == "degraded"
        assert result.providers["cerebras"].status == "healthy"
        assert result.providers["bedrock"].status == "unhealthy"


@pytest.mark.asyncio
async def test_health_check_all_unhealthy() -> None:
    """Test health check when all providers are unhealthy."""
    mock_cerebras = AsyncMock()
    mock_cerebras.health_check = AsyncMock(
        return_value={"status": "unhealthy", "provider": "cerebras"}
    )

    mock_bedrock = AsyncMock()
    mock_bedrock.health_check = AsyncMock(
        return_value={"status": "unhealthy", "provider": "bedrock"}
    )

    def mock_get_adapter(provider: str):  # type: ignore[no-untyped-def]
        if provider == "cerebras":
            return mock_cerebras
        return mock_bedrock

    with patch("unifiedai._health.get_adapter", side_effect=mock_get_adapter):
        result = await health_check(["cerebras", "bedrock"])

        # When all are unhealthy, overall status should be "unhealthy"
        assert result.status == "unhealthy"
        assert result.providers["cerebras"].status == "unhealthy"
        assert result.providers["bedrock"].status == "unhealthy"


@pytest.mark.asyncio
async def test_health_check_with_exception() -> None:
    """Test health check when adapter raises exception."""
    mock_cerebras = AsyncMock()
    mock_cerebras.health_check = AsyncMock(side_effect=Exception("Connection failed"))

    with patch("unifiedai._health.get_adapter", return_value=mock_cerebras):
        result = await health_check(["cerebras"])

        # When an exception is raised, it counts as unhealthy for all providers
        assert result.status == "unhealthy"
        assert result.providers["cerebras"].status == "unhealthy"


@pytest.mark.asyncio
async def test_health_check_empty_adapters() -> None:
    """Test health check with no adapters."""
    result = await health_check([])

    assert result.status == "healthy"  # No adapters means healthy by default
    assert len(result.providers) == 0


def test_provider_health_model() -> None:
    """Test ProviderHealth model."""
    health = ProviderHealth(
        provider="cerebras",
        status="healthy",
    )
    assert health.provider == "cerebras"
    assert health.status == "healthy"
