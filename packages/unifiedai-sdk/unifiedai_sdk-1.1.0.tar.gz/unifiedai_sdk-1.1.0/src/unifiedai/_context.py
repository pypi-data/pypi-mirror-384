"""Request-scoped context and correlation ID helpers."""

from __future__ import annotations

import uuid
from dataclasses import dataclass


@dataclass
class RequestContext:
    correlation_id: str

    @classmethod
    def new(cls) -> RequestContext:
        return cls(correlation_id=str(uuid.uuid4()))

    def headers(self) -> dict[str, str]:
        return {
            "X-Correlation-ID": self.correlation_id,
            "X-Request-ID": self.correlation_id,
        }
