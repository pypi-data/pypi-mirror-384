from __future__ import annotations

__version__ = "1.0.2"

from ._async_client import AsyncUnifiedAI
from ._bedrock_compat import BedrockConverseResponse, BedrockRuntime
from ._cerebras_compat import AsyncCerebras, Cerebras
from ._client import UnifiedClient as UnifiedAI
from ._exceptions import (
    APIError,
    AuthenticationError,
    BadRequestError,
    ComparisonError,
    ConflictError,
    ConnectionError,
    InternalServerError,
    InvalidRequestError,
    NotFoundError,
    PermissionDeniedError,
    ProviderError,
    RateLimitError,
    SDKError,
    ServiceUnavailableError,
    TimeoutError,
    UnprocessableEntityError,
    map_http_status_to_exception,
)
from ._health import health_check

__all__ = [
    # Clients
    "UnifiedAI",
    "AsyncUnifiedAI",
    "Cerebras",
    "AsyncCerebras",
    "BedrockRuntime",
    "BedrockConverseResponse",
    # Health
    "health_check",
    # Base Exceptions
    "SDKError",
    "APIError",
    "ProviderError",
    # 4xx Client Errors
    "BadRequestError",
    "AuthenticationError",
    "PermissionDeniedError",
    "NotFoundError",
    "ConflictError",
    "UnprocessableEntityError",
    "RateLimitError",
    # 5xx Server Errors
    "InternalServerError",
    "ServiceUnavailableError",
    # Network Errors
    "ConnectionError",
    "TimeoutError",
    # SDK-Specific Errors
    "InvalidRequestError",
    "ComparisonError",
    # Helper Functions
    "map_http_status_to_exception",
    # Version
    "__version__",
]
