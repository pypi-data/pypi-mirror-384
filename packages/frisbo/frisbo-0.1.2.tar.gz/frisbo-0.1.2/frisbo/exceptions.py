"""Custom exceptions for Frisbo SDK."""


class FrisboError(Exception):
    """Base exception for all Frisbo SDK errors."""
    pass


class AuthenticationError(FrisboError):
    """Raised when authentication fails."""
    pass


class APIError(FrisboError):
    """Raised when the API returns an error response."""

    def __init__(self, message: str, status_code: int = None, response: dict = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class ValidationError(FrisboError):
    """Raised when request validation fails."""
    pass


class NotFoundError(APIError):
    """Raised when a resource is not found (404)."""
    pass


class RateLimitError(APIError):
    """Raised when rate limit is exceeded."""
    pass
