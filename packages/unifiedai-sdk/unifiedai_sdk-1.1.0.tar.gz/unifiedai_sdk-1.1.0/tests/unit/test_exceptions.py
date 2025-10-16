"""Test custom exception classes and error handling."""

from __future__ import annotations

from unifiedai._exceptions import (
    AuthenticationError,
    ComparisonError,
    InvalidRequestError,
    ProviderError,
    RateLimitError,
    SDKError,
    TimeoutError,
)


def test_sdk_error_base() -> None:
    """Test base SDKError exception."""
    error = SDKError("Test error")
    assert str(error) == "Test error"
    assert isinstance(error, Exception)


def test_provider_error_with_message() -> None:
    """Test ProviderError with custom message."""
    original = Exception("Original error")
    error = ProviderError(provider="cerebras", original_error=original)
    error_str = str(error)
    assert "cerebras" in error_str
    assert "Original error" in error_str


def test_authentication_error() -> None:
    """Test AuthenticationError formatting."""
    error = AuthenticationError(
        message="Invalid API key", request_id="test_123", provider="cerebras", status_code=401
    )
    error_str = str(error)
    assert "cerebras" in error_str.lower()
    assert "invalid api key" in error_str.lower()
    assert "401" in error_str


def test_rate_limit_error_without_retry_after() -> None:
    """Test RateLimitError without retry_after."""
    error = RateLimitError(
        message="Rate limit exceeded", request_id="test_123", provider="bedrock", status_code=429
    )
    error_str = str(error)
    assert "rate limit" in error_str.lower()
    assert "bedrock" in error_str.lower()
    assert "429" in error_str


def test_rate_limit_error_with_retry_after() -> None:
    """Test RateLimitError with retry_after."""
    error = RateLimitError(
        message="Rate limit exceeded",
        request_id="test_123",
        provider="bedrock",
        status_code=429,
        retry_after=30,
    )
    error_str = str(error)
    assert "30" in error_str
    assert "retry after" in error_str.lower()


def test_timeout_error() -> None:
    """Test TimeoutError formatting."""
    error = TimeoutError(
        message="Request timed out after 60s",
        request_id="test_123",
        provider="cerebras",
        status_code=408,
        timeout_seconds=60,
    )
    error_str = str(error)
    assert "timeout" in error_str.lower()
    assert "cerebras" in error_str.lower()
    assert "60" in error_str


def test_invalid_request_error() -> None:
    """Test InvalidRequestError."""
    error = InvalidRequestError("Invalid model name")
    error_str = str(error)
    assert "Invalid model name" in error_str


def test_comparison_error_partial_failure() -> None:
    """Test ComparisonError with partial failure."""
    error = ComparisonError(
        successful_provider="cerebras",
        failed_provider="bedrock",
    )
    error_str = str(error)
    assert "partial failure" in error_str.lower()
    assert "cerebras" in error_str
    assert "bedrock" in error_str
    assert "succeeded" in error_str


def test_comparison_error_only_failed() -> None:
    """Test ComparisonError with only failed provider."""
    error = ComparisonError(failed_provider="bedrock")
    error_str = str(error)
    assert "bedrock" in error_str
    assert "failed" in error_str


def test_comparison_error_no_details() -> None:
    """Test ComparisonError with no details."""
    error = ComparisonError()
    error_str = str(error)
    assert "Comparison failed" in error_str
