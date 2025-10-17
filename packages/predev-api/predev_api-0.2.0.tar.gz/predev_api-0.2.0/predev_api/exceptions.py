"""
Custom exceptions for the Pre.dev API client
"""


class PredevAPIError(Exception):
    """Base exception for Pre.dev API errors."""
    pass


class AuthenticationError(PredevAPIError):
    """Raised when authentication fails."""
    pass


class RateLimitError(PredevAPIError):
    """Raised when rate limit is exceeded."""
    pass
