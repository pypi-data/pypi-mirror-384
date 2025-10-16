"""Unified error hierarchy for the SDK.

This module provides a comprehensive exception hierarchy following industry best practices
(inspired by OpenAI SDK). All exceptions include request_id tracking for better debugging
and support correlation.

Exception Hierarchy:
    SDKError (base)
    ├── APIError (base for all API-related errors)
    │   ├── ProviderError (provider-specific errors)
    │   │   ├── BadRequestError (400)
    │   │   ├── AuthenticationError (401)
    │   │   ├── PermissionDeniedError (403)
    │   │   ├── NotFoundError (404)
    │   │   ├── ConflictError (409)
    │   │   ├── UnprocessableEntityError (422)
    │   │   ├── RateLimitError (429)
    │   │   ├── InternalServerError (500+)
    │   │   └── ServiceUnavailableError (503)
    │   ├── ConnectionError (network issues)
    │   └── TimeoutError (request timeout)
    ├── InvalidRequestError (invalid parameters)
    └── ComparisonError (comparison mode failures)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class SDKError(Exception):
    """Base exception for all SDK errors.

    Attributes:
        message: Human-readable error message
        request_id: Optional request ID for correlation and debugging
    """

    def __init__(self, message: str = "", request_id: str | None = None) -> None:
        """Initialize SDK error.

        Args:
            message: Human-readable error message
            request_id: Optional request ID for correlation
        """
        super().__init__(message)
        self.message = message
        self.request_id = request_id

    def __str__(self) -> str:
        """Return human-readable error message."""
        if self.request_id:
            return f"{self.message} (request_id: {self.request_id})"
        return self.message


class APIError(SDKError):
    """Base exception for all API-related errors.

    Attributes:
        message: Human-readable error message
        request_id: Optional request ID for correlation
        status_code: HTTP status code (if applicable)
        response_body: Raw response body (if available)
    """

    def __init__(
        self,
        message: str = "",
        request_id: str | None = None,
        status_code: int | None = None,
        response_body: Any | None = None,
    ) -> None:
        """Initialize API error.

        Args:
            message: Human-readable error message
            request_id: Optional request ID for correlation
            status_code: HTTP status code
            response_body: Raw response body
        """
        super().__init__(message, request_id)
        self.status_code = status_code
        self.response_body = response_body

    def __str__(self) -> str:
        """Return human-readable error message."""
        parts = [self.message]
        if self.status_code:
            parts.append(f"status_code: {self.status_code}")
        if self.request_id:
            parts.append(f"request_id: {self.request_id}")
        return f"{parts[0]} ({', '.join(parts[1:])})" if len(parts) > 1 else parts[0]


@dataclass
class ProviderError(APIError):
    """Provider-specific error with original error details.

    Attributes:
        provider: Provider identifier (e.g., "cerebras", "bedrock")
        message: Human-readable error message
        original_error: The underlying exception that caused this error
        request_id: Optional request ID for correlation
        status_code: HTTP status code (if applicable)
        response_body: Raw response body (if available)
    """

    provider: str = ""
    message: str = ""
    original_error: Exception | None = None
    request_id: str | None = None
    status_code: int | None = None
    response_body: Any | None = None

    def __post_init__(self) -> None:
        """Initialize base APIError after dataclass initialization."""
        if not self.message and self.original_error:
            self.message = str(self.original_error)
        elif not self.message:
            self.message = f"Provider '{self.provider}' error"

    def __str__(self) -> str:
        """Return human-readable error message."""
        parts = [f"Provider '{self.provider}' error"]
        if self.original_error:
            parts[0] = f"Provider '{self.provider}' error: {str(self.original_error)}"
        elif self.message and self.message != f"Provider '{self.provider}' error":
            parts[0] = f"Provider '{self.provider}': {self.message}"

        if self.status_code:
            parts.append(f"status_code: {self.status_code}")
        if self.request_id:
            parts.append(f"request_id: {self.request_id}")

        return f"{parts[0]} ({', '.join(parts[1:])})" if len(parts) > 1 else parts[0]


# ============================================================================
# HTTP Status-Specific Errors (4xx Client Errors)
# ============================================================================


@dataclass
class BadRequestError(ProviderError):
    """HTTP 400 Bad Request error.

    Raised when the request is malformed or contains invalid parameters.

    Example:
        >>> raise BadRequestError(
        ...     provider="cerebras",
        ...     message="Invalid temperature value",
        ...     status_code=400,
        ...     request_id="req_123"
        ... )
    """

    def __post_init__(self) -> None:
        """Initialize with default message if not provided."""
        if not self.message:
            self.message = "Bad request - invalid parameters"
        if not self.status_code:
            self.status_code = 400
        super().__post_init__()


@dataclass
class AuthenticationError(ProviderError):
    """HTTP 401 Unauthorized error.

    Raised when authentication fails or API key is invalid.

    Example:
        >>> raise AuthenticationError(
        ...     provider="cerebras",
        ...     message="Invalid API key",
        ...     status_code=401
        ... )
    """

    def __post_init__(self) -> None:
        """Initialize with default message if not provided."""
        if not self.message:
            self.message = "Authentication failed - invalid or missing credentials"
        if not self.status_code:
            self.status_code = 401
        super().__post_init__()


@dataclass
class PermissionDeniedError(ProviderError):
    """HTTP 403 Forbidden error.

    Raised when the user lacks permission to access the resource.

    Example:
        >>> raise PermissionDeniedError(
        ...     provider="bedrock",
        ...     message="Insufficient permissions for model access",
        ...     status_code=403
        ... )
    """

    def __post_init__(self) -> None:
        """Initialize with default message if not provided."""
        if not self.message:
            self.message = "Permission denied - insufficient privileges"
        if not self.status_code:
            self.status_code = 403
        super().__post_init__()


@dataclass
class NotFoundError(ProviderError):
    """HTTP 404 Not Found error.

    Raised when the requested resource (model, endpoint) does not exist.

    Example:
        >>> raise NotFoundError(
        ...     provider="cerebras",
        ...     message="Model 'invalid-model' not found",
        ...     status_code=404
        ... )
    """

    def __post_init__(self) -> None:
        """Initialize with default message if not provided."""
        if not self.message:
            self.message = "Resource not found"
        if not self.status_code:
            self.status_code = 404
        super().__post_init__()


@dataclass
class ConflictError(ProviderError):
    """HTTP 409 Conflict error.

    Raised when the request conflicts with the current state of the resource.

    Example:
        >>> raise ConflictError(
        ...     provider="bedrock",
        ...     message="Resource already exists",
        ...     status_code=409
        ... )
    """

    def __post_init__(self) -> None:
        """Initialize with default message if not provided."""
        if not self.message:
            self.message = "Conflict - request conflicts with current state"
        if not self.status_code:
            self.status_code = 409
        super().__post_init__()


@dataclass
class UnprocessableEntityError(ProviderError):
    """HTTP 422 Unprocessable Entity error.

    Raised when the request is well-formed but contains semantic errors.

    Example:
        >>> raise UnprocessableEntityError(
        ...     provider="cerebras",
        ...     message="Temperature must be between 0 and 2",
        ...     status_code=422
        ... )
    """

    def __post_init__(self) -> None:
        """Initialize with default message if not provided."""
        if not self.message:
            self.message = "Unprocessable entity - semantic validation failed"
        if not self.status_code:
            self.status_code = 422
        super().__post_init__()


@dataclass
class RateLimitError(ProviderError):
    """HTTP 429 Too Many Requests error.

    Raised when the rate limit is exceeded.

    Attributes:
        retry_after: Seconds to wait before retrying (from Retry-After header)

    Example:
        >>> raise RateLimitError(
        ...     provider="cerebras",
        ...     message="Rate limit exceeded",
        ...     status_code=429,
        ...     retry_after=60
        ... )
    """

    retry_after: int | None = None

    def __post_init__(self) -> None:
        """Initialize with default message if not provided."""
        if not self.message:
            self.message = "Rate limit exceeded"
        if not self.status_code:
            self.status_code = 429
        super().__post_init__()

    def __str__(self) -> str:
        """Return human-readable error message."""
        base_msg = f"Provider '{self.provider}' rate limit exceeded"
        parts = []

        if self.retry_after:
            parts.append(f"retry after {self.retry_after}s")
        if self.status_code:
            parts.append(f"status_code: {self.status_code}")
        if self.request_id:
            parts.append(f"request_id: {self.request_id}")

        return f"{base_msg} ({', '.join(parts)})" if parts else base_msg


# ============================================================================
# HTTP Status-Specific Errors (5xx Server Errors)
# ============================================================================


@dataclass
class InternalServerError(ProviderError):
    """HTTP 500+ Internal Server Error.

    Raised when the provider experiences an internal error (500, 502, 504, etc.).

    Example:
        >>> raise InternalServerError(
        ...     provider="bedrock",
        ...     message="Internal server error",
        ...     status_code=500
        ... )
    """

    def __post_init__(self) -> None:
        """Initialize with default message if not provided."""
        if not self.message:
            self.message = "Internal server error"
        if not self.status_code:
            self.status_code = 500
        super().__post_init__()


@dataclass
class ServiceUnavailableError(ProviderError):
    """HTTP 503 Service Unavailable error.

    Raised when the provider service is temporarily unavailable.

    Attributes:
        retry_after: Seconds to wait before retrying (from Retry-After header)

    Example:
        >>> raise ServiceUnavailableError(
        ...     provider="cerebras",
        ...     message="Service temporarily unavailable",
        ...     status_code=503,
        ...     retry_after=30
        ... )
    """

    retry_after: int | None = None

    def __post_init__(self) -> None:
        """Initialize with default message if not provided."""
        if not self.message:
            self.message = "Service temporarily unavailable"
        if not self.status_code:
            self.status_code = 503
        super().__post_init__()

    def __str__(self) -> str:
        """Return human-readable error message."""
        base_msg = f"Provider '{self.provider}' service unavailable"
        parts = []

        if self.retry_after:
            parts.append(f"retry after {self.retry_after}s")
        if self.status_code:
            parts.append(f"status_code: {self.status_code}")
        if self.request_id:
            parts.append(f"request_id: {self.request_id}")

        return f"{base_msg} ({', '.join(parts)})" if parts else base_msg


# ============================================================================
# Network and Timeout Errors
# ============================================================================


@dataclass
class ConnectionError(APIError):
    """Network connection error.

    Raised when unable to establish a connection to the provider.

    Attributes:
        provider: Provider identifier
        original_error: The underlying connection exception

    Example:
        >>> raise ConnectionError(
        ...     message="Failed to connect to cerebras.ai",
        ...     request_id="req_123"
        ... )
    """

    provider: str = ""
    original_error: Exception | None = None

    def __post_init__(self) -> None:
        """Initialize with default message if not provided."""
        if not self.message and self.original_error:
            self.message = f"Connection failed: {str(self.original_error)}"
        elif not self.message:
            self.message = "Connection failed"

    def __str__(self) -> str:
        """Return human-readable error message."""
        parts = [self.message]
        if self.provider:
            parts[0] = f"Provider '{self.provider}' connection failed"
            if self.original_error:
                parts[0] += f": {str(self.original_error)}"
        if self.request_id:
            parts.append(f"request_id: {self.request_id}")

        return f"{parts[0]} ({', '.join(parts[1:])})" if len(parts) > 1 else parts[0]


class TimeoutError(APIError):
    """Request timeout error.

    Raised when a request exceeds the configured timeout.

    Attributes:
        provider: Provider identifier
        timeout_seconds: Timeout duration that was exceeded

    Example:
        >>> raise TimeoutError(
        ...     message="Request timed out after 60s",
        ...     request_id="req_123",
        ...     timeout_seconds=60
        ... )
    """

    def __init__(
        self,
        message: str = "",
        request_id: str | None = None,
        status_code: int | None = None,
        provider: str = "",
        timeout_seconds: float | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize timeout error."""
        # Generate default message if not provided
        if not message and timeout_seconds:
            message = f"Request timed out after {timeout_seconds}s"
        elif not message:
            message = "Request timed out"

        super().__init__(message, request_id, status_code)
        self.provider = provider
        self.timeout_seconds = timeout_seconds

    def __str__(self) -> str:
        """Return human-readable error message."""
        parts = [self.message]
        if self.provider:
            parts[0] = f"Provider '{self.provider}' timeout: {self.message}"
        if self.request_id:
            parts.append(f"request_id: {self.request_id}")
        if self.status_code:
            parts.append(f"status_code: {self.status_code}")

        return f"{parts[0]} ({', '.join(parts[1:])})" if len(parts) > 1 else parts[0]


# ============================================================================
# SDK-Specific Errors
# ============================================================================


class InvalidRequestError(SDKError):
    """Invalid request parameters.

    Raised when request validation fails before sending to provider.

    Example:
        >>> raise InvalidRequestError(
        ...     message="Temperature must be between 0 and 2",
        ...     request_id="req_123"
        ... )
    """

    def __init__(self, message: str = "Invalid request", request_id: str | None = None):
        """Initialize invalid request error.

        Args:
            message: Error message
            request_id: Optional request ID for correlation
        """
        super().__init__(message, request_id)
        self.message = message


@dataclass
class ComparisonError(SDKError):
    """Comparison mode error.

    Raised when comparison mode encounters failures.

    Attributes:
        message: Human-readable error message
        request_id: Optional request ID for correlation
        successful_provider: Provider that succeeded (if any)
        failed_provider: Provider that failed (if any)

    Example:
        >>> raise ComparisonError(
        ...     message="Comparison partial failure",
        ...     request_id="req_123",
        ...     successful_provider="cerebras",
        ...     failed_provider="bedrock"
        ... )
    """

    message: str = ""
    request_id: str | None = None
    successful_provider: str | None = None
    failed_provider: str | None = None

    def __post_init__(self) -> None:
        """Initialize with default message if not provided."""
        if not self.message:
            if self.successful_provider and self.failed_provider:
                self.message = (
                    f"Comparison partial failure: '{self.failed_provider}' failed, "
                    f"'{self.successful_provider}' succeeded"
                )
            elif self.failed_provider:
                self.message = f"Comparison failed for provider '{self.failed_provider}'"
            else:
                self.message = "Comparison failed"

    def __str__(self) -> str:
        """Return human-readable error message."""
        if self.request_id:
            return f"{self.message} (request_id: {self.request_id})"
        return self.message


# ============================================================================
# Helper Functions
# ============================================================================


def map_http_status_to_exception(
    status_code: int,
    provider: str,
    message: str = "",
    request_id: str | None = None,
    response_body: Any | None = None,
    original_error: Exception | None = None,
) -> ProviderError:
    """Map HTTP status code to appropriate exception type.

    This function follows industry best practices by mapping specific HTTP
    status codes to dedicated exception classes for better error handling.

    Args:
        status_code: HTTP status code from provider response
        provider: Provider identifier (e.g., "cerebras", "bedrock")
        message: Human-readable error message
        request_id: Optional request ID for correlation
        response_body: Raw response body (if available)
        original_error: The underlying exception (if any)

    Returns:
        Appropriate ProviderError subclass based on status code

    Example:
        >>> exception = map_http_status_to_exception(
        ...     status_code=401,
        ...     provider="cerebras",
        ...     message="Invalid API key",
        ...     request_id="req_123"
        ... )
        >>> isinstance(exception, AuthenticationError)
        True
    """
    # Map status codes to exception classes
    # We explicitly construct each exception to avoid mypy errors with **kwargs
    if status_code == 400:
        return BadRequestError(
            provider=provider,
            message=message,
            request_id=request_id,
            status_code=status_code,
            response_body=response_body,
            original_error=original_error,
        )
    elif status_code == 401:
        return AuthenticationError(
            provider=provider,
            message=message,
            request_id=request_id,
            status_code=status_code,
            response_body=response_body,
            original_error=original_error,
        )
    elif status_code == 403:
        return PermissionDeniedError(
            provider=provider,
            message=message,
            request_id=request_id,
            status_code=status_code,
            response_body=response_body,
            original_error=original_error,
        )
    elif status_code == 404:
        return NotFoundError(
            provider=provider,
            message=message,
            request_id=request_id,
            status_code=status_code,
            response_body=response_body,
            original_error=original_error,
        )
    elif status_code == 409:
        return ConflictError(
            provider=provider,
            message=message,
            request_id=request_id,
            status_code=status_code,
            response_body=response_body,
            original_error=original_error,
        )
    elif status_code == 422:
        return UnprocessableEntityError(
            provider=provider,
            message=message,
            request_id=request_id,
            status_code=status_code,
            response_body=response_body,
            original_error=original_error,
        )
    elif status_code == 429:
        return RateLimitError(
            provider=provider,
            message=message,
            request_id=request_id,
            status_code=status_code,
            response_body=response_body,
            original_error=original_error,
        )
    elif status_code == 503:
        return ServiceUnavailableError(
            provider=provider,
            message=message,
            request_id=request_id,
            status_code=status_code,
            response_body=response_body,
            original_error=original_error,
        )
    elif status_code >= 500:
        return InternalServerError(
            provider=provider,
            message=message,
            request_id=request_id,
            status_code=status_code,
            response_body=response_body,
            original_error=original_error,
        )
    else:
        # For unknown status codes, return generic ProviderError
        return ProviderError(
            provider=provider,
            message=message,
            request_id=request_id,
            status_code=status_code,
            response_body=response_body,
            original_error=original_error,
        )


__all__ = [
    # Base exceptions
    "SDKError",
    "APIError",
    "ProviderError",
    # 4xx Client errors
    "BadRequestError",
    "AuthenticationError",
    "PermissionDeniedError",
    "NotFoundError",
    "ConflictError",
    "UnprocessableEntityError",
    "RateLimitError",
    # 5xx Server errors
    "InternalServerError",
    "ServiceUnavailableError",
    # Network errors
    "ConnectionError",
    "TimeoutError",
    # SDK-specific errors
    "InvalidRequestError",
    "ComparisonError",
    # Helper functions
    "map_http_status_to_exception",
]
