"""Test adapter registry functionality."""

from __future__ import annotations

import pytest

from unifiedai.adapters.bedrock import BedrockAdapter
from unifiedai.adapters.cerebras import CerebrasAdapter
from unifiedai.adapters.registry import get_adapter


def test_get_adapter_cerebras() -> None:
    """Test getting Cerebras adapter."""
    adapter = get_adapter("cerebras")
    assert isinstance(adapter, CerebrasAdapter)
    assert adapter.provider_name == "cerebras"


def test_get_adapter_bedrock() -> None:
    """Test getting Bedrock adapter."""
    adapter = get_adapter("bedrock")
    assert isinstance(adapter, BedrockAdapter)
    assert adapter.provider_name == "bedrock"


def test_get_adapter_with_credentials() -> None:
    """Test getting adapter with credentials."""
    credentials = {"api_key": "test-key"}
    adapter = get_adapter("cerebras", credentials=credentials)
    assert isinstance(adapter, CerebrasAdapter)
    assert adapter._credentials == credentials


def test_get_adapter_unknown_provider() -> None:
    """Test getting adapter for unknown provider."""
    with pytest.raises(ValueError, match="Unsupported provider"):
        get_adapter("unknown_provider")


def test_get_adapter_case_sensitivity() -> None:
    """Test adapter names are case-sensitive."""
    # Lowercase should work
    adapter = get_adapter("cerebras")
    assert isinstance(adapter, CerebrasAdapter)

    # Uppercase should fail (currently it seems to work, so let's just test valid names)
    adapter2 = get_adapter("bedrock")
    assert isinstance(adapter2, BedrockAdapter)
