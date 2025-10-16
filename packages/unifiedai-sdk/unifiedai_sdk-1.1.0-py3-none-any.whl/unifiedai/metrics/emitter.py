"""Prometheus metrics definitions for SDK telemetry."""

from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram

requests_total = Counter(
    "sdk_requests_total",
    "Total requests",
    ["provider", "model", "status"],
)

request_duration_seconds = Histogram(
    "sdk_request_duration_seconds",
    "Request duration",
    ["provider", "model"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0],
)

ttfb_seconds = Histogram(
    "sdk_ttfb_seconds",
    "Time to first byte",
    ["provider", "model"],
)

active_requests = Gauge(
    "sdk_active_requests",
    "Active requests",
    ["provider"],
)
