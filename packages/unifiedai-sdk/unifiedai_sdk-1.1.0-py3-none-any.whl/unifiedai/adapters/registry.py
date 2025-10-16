"""Provider adapter registry/factory.

Maps provider strings to adapter classes. Extend this module to register new
providers without changing the client code.
"""

from __future__ import annotations

from .base import BaseAdapter
from .bedrock import BedrockAdapter
from .cerebras import CerebrasAdapter


def get_adapter(provider: str, *, credentials: dict[str, str] | None = None) -> BaseAdapter:
    name = provider.lower()
    if name == "cerebras":
        return CerebrasAdapter(credentials=credentials)
    if name == "bedrock":
        return BedrockAdapter(credentials=credentials)
    raise ValueError(f"Unsupported provider: {provider}")
