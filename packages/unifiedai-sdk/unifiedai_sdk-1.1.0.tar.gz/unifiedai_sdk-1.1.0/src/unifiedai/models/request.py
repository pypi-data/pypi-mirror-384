"""Request models for chat completions.

Defines ``Message`` and ``ChatRequest`` with strict Pydantic validation.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Message(BaseModel):
    model_config = ConfigDict(strict=True)
    role: Literal["system", "user", "assistant"] = Field(..., description="Message role")
    content: str = Field(..., min_length=1, description="Message content")


class ChatRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    provider: str = Field(..., description="Provider name (e.g., 'cerebras', 'bedrock')")
    model: str = Field(..., min_length=1, description="Model identifier (e.g., 'llama3.1-8b')")
    messages: list[Message] = Field(..., min_length=1, description="Conversation messages")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: int = Field(256, gt=0, le=32000, description="Maximum tokens to generate")
