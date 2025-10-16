"""Streaming delta model for chat completions."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class StreamChunk(BaseModel):
    model_config = ConfigDict(strict=True)

    id: str
    model: str
    index: int
    delta: dict[str, str]
    finish_reason: str | None = None
