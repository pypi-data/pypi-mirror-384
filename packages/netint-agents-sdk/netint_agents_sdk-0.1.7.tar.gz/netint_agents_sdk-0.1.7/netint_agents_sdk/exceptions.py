"""
Custom exceptions for the NetInt Agents SDK.
"""

from typing import Any, Dict, Optional


class NetIntAPIError(Exception):
    """Base exception for all NetInt API errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.response = response
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.status_code:
            return f"[{self.status_code}] {self.message}"
        return self.message


class AuthenticationError(NetIntAPIError):
    """Raised when authentication fails or token is invalid."""
    pass


class PermissionError(NetIntAPIError):
    """Raised when user lacks permission for the requested operation."""
    pass


class ResourceNotFoundError(NetIntAPIError):
    """Raised when a requested resource is not found."""
    pass


class ValidationError(NetIntAPIError):
    """Raised when request validation fails."""

    def __init__(
        self,
        message: str,
        validation_errors: Optional[list] = None,
        status_code: Optional[int] = None,
        response: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, status_code, response)
        self.validation_errors = validation_errors or []


class RateLimitError(NetIntAPIError):
    """Raised when rate limit is exceeded."""

    def __init__(
        self,
        message: str,
        retry_after: Optional[int] = None,
        status_code: Optional[int] = None,
        response: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, status_code, response)
        self.retry_after = retry_after


class ServerError(NetIntAPIError):
    """Raised when server returns a 5xx error."""
    pass


class TimeoutError(NetIntAPIError):
    """Raised when a request times out."""
    pass


class ConnectionError(NetIntAPIError):
    """Raised when connection to the API fails."""
    pass
