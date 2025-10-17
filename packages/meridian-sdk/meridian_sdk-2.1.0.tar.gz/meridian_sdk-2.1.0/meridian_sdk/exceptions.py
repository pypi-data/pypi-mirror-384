"""
Meridian SDK Exceptions

Custom exception classes for the Meridian SDK.
"""

from typing import Optional, Dict, Any


class MeridianError(Exception):
    """Base exception for all Meridian SDK errors"""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response = response

    def __str__(self) -> str:
        if self.status_code:
            return f"[{self.status_code}] {self.message}"
        return self.message


class AuthenticationError(MeridianError):
    """Raised when API key authentication fails"""
    pass


class RateLimitError(MeridianError):
    """Raised when rate limit is exceeded"""

    def __init__(
        self,
        message: str,
        retry_after: Optional[int] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        self.retry_after = retry_after


class ValidationError(MeridianError):
    """Raised when request validation fails"""
    pass


class NotFoundError(MeridianError):
    """Raised when requested resource is not found"""
    pass


class ServerError(MeridianError):
    """Raised when server returns 5xx error"""
    pass


class MeridianTimeoutError(MeridianError):
    """Raised when request times out"""
    pass


class MeridianConnectionError(MeridianError):
    """Raised when connection to API fails"""
    pass
