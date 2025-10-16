"""Structured logging configuration (structlog) with redaction."""

from __future__ import annotations

import structlog


def _add_redaction(_, __, event_dict):  # type: ignore[no-untyped-def]
    sensitive_keys = {"api_key", "token", "secret", "authorization"}
    for k in list(event_dict.keys()):
        if k.lower() in sensitive_keys:
            event_dict[k] = "***REDACTED***"
    return event_dict


structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        _add_redaction,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
)

logger = structlog.get_logger()
