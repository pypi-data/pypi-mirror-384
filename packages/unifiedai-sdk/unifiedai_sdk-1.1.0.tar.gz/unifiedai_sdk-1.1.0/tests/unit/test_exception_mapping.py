"""Test exception mapping from HTTP status codes."""

from __future__ import annotations

from unifiedai._exceptions import (
    APIError,
    AuthenticationError,
    BadRequestError,
    ConflictError,
    InternalServerError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitError,
    ServiceUnavailableError,
    UnprocessableEntityError,
    map_http_status_to_exception,
)


class TestHTTPStatusMapping:
    """Test HTTP status code to exception mapping."""

    def test_400_bad_request(self) -> None:
        """Test 400 status code maps to BadRequestError."""
        exc = map_http_status_to_exception(
            status_code=400,
            message="Bad request",
            request_id="test-123",
            provider="cerebras",
        )
        assert isinstance(exc, BadRequestError)
        assert exc.status_code == 400
        assert exc.request_id == "test-123"

    def test_401_authentication(self) -> None:
        """Test 401 status code maps to AuthenticationError."""
        exc = map_http_status_to_exception(
            status_code=401,
            message="Unauthorized",
            request_id="test-123",
            provider="cerebras",
        )
        assert isinstance(exc, AuthenticationError)
        assert exc.status_code == 401

    def test_403_permission_denied(self) -> None:
        """Test 403 status code maps to PermissionDeniedError."""
        exc = map_http_status_to_exception(
            status_code=403,
            message="Forbidden",
            request_id="test-123",
            provider="cerebras",
        )
        assert isinstance(exc, PermissionDeniedError)
        assert exc.status_code == 403

    def test_404_not_found(self) -> None:
        """Test 404 status code maps to NotFoundError."""
        exc = map_http_status_to_exception(
            status_code=404,
            message="Not found",
            request_id="test-123",
            provider="cerebras",
        )
        assert isinstance(exc, NotFoundError)
        assert exc.status_code == 404

    def test_409_conflict(self) -> None:
        """Test 409 status code maps to ConflictError."""
        exc = map_http_status_to_exception(
            status_code=409,
            message="Conflict",
            request_id="test-123",
            provider="cerebras",
        )
        assert isinstance(exc, ConflictError)
        assert exc.status_code == 409

    def test_422_unprocessable_entity(self) -> None:
        """Test 422 status code maps to UnprocessableEntityError."""
        exc = map_http_status_to_exception(
            status_code=422,
            message="Unprocessable",
            request_id="test-123",
            provider="cerebras",
        )
        assert isinstance(exc, UnprocessableEntityError)
        assert exc.status_code == 422

    def test_429_rate_limit(self) -> None:
        """Test 429 status code maps to RateLimitError."""
        exc = map_http_status_to_exception(
            status_code=429,
            message="Rate limit exceeded",
            request_id="test-123",
            provider="cerebras",
        )
        assert isinstance(exc, RateLimitError)
        assert exc.status_code == 429

    def test_500_internal_server_error(self) -> None:
        """Test 500 status code maps to InternalServerError."""
        exc = map_http_status_to_exception(
            status_code=500,
            message="Internal error",
            request_id="test-123",
            provider="cerebras",
        )
        assert isinstance(exc, InternalServerError)
        assert exc.status_code == 500

    def test_503_service_unavailable(self) -> None:
        """Test 503 status code maps to ServiceUnavailableError."""
        exc = map_http_status_to_exception(
            status_code=503,
            message="Service unavailable",
            request_id="test-123",
            provider="cerebras",
        )
        assert isinstance(exc, ServiceUnavailableError)
        assert exc.status_code == 503

    def test_unknown_status_code(self) -> None:
        """Test unknown status code maps to generic APIError."""
        exc = map_http_status_to_exception(
            status_code=418,  # I'm a teapot
            message="Unknown error",
            request_id="test-123",
            provider="cerebras",
        )
        assert isinstance(exc, APIError)
        assert exc.status_code == 418


class TestExceptionStringRepresentation:
    """Test exception string representations."""

    def test_bad_request_str(self) -> None:
        """Test BadRequestError string representation."""
        error = BadRequestError(
            message="Invalid parameter",
            request_id="test-123",
            provider="cerebras",
            status_code=400,
        )
        error_str = str(error)
        assert "400" in error_str
        assert "test-123" in error_str
        assert "Invalid parameter" in error_str

    def test_permission_denied_str(self) -> None:
        """Test PermissionDeniedError string representation."""
        error = PermissionDeniedError(
            message="Access denied",
            request_id="test-123",
            provider="bedrock",
            status_code=403,
        )
        error_str = str(error)
        assert "403" in error_str
        assert "Access denied" in error_str

    def test_not_found_str(self) -> None:
        """Test NotFoundError string representation."""
        error = NotFoundError(
            message="Resource not found",
            request_id="test-123",
            provider="cerebras",
            status_code=404,
        )
        error_str = str(error)
        assert "404" in error_str
        assert "Resource not found" in error_str

    def test_conflict_str(self) -> None:
        """Test ConflictError string representation."""
        error = ConflictError(
            message="Resource conflict",
            request_id="test-123",
            provider="cerebras",
            status_code=409,
        )
        error_str = str(error)
        assert "409" in error_str
        assert "Resource conflict" in error_str

    def test_unprocessable_entity_str(self) -> None:
        """Test UnprocessableEntityError string representation."""
        error = UnprocessableEntityError(
            message="Invalid data",
            request_id="test-123",
            provider="cerebras",
            status_code=422,
        )
        error_str = str(error)
        assert "422" in error_str
        assert "Invalid data" in error_str

    def test_internal_server_error_str(self) -> None:
        """Test InternalServerError string representation."""
        error = InternalServerError(
            message="Server error",
            request_id="test-123",
            provider="cerebras",
            status_code=500,
        )
        error_str = str(error)
        assert "500" in error_str
        assert "Server error" in error_str

    def test_service_unavailable_str(self) -> None:
        """Test ServiceUnavailableError string representation."""
        error = ServiceUnavailableError(
            message="Service down",
            request_id="test-123",
            provider="bedrock",
            status_code=503,
        )
        error_str = str(error)
        assert "503" in error_str
        assert "service unavailable" in error_str.lower()
