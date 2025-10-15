"""StockAlert SDK Exceptions."""
from typing import Dict, Optional


class StockAlertError(Exception):
    """Base exception for StockAlert SDK."""
    pass


class APIError(StockAlertError):
    """API error response."""

    def __init__(self, message: str, status_code: Optional[int] = None, response: Optional[Dict] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response or {}


class RateLimitError(APIError):
    """Rate limit exceeded error."""

    def __init__(self, message: str, retry_after: Optional[int] = None):
        super().__init__(message, 429)
        self.retry_after = retry_after


class AuthenticationError(APIError):
    """Authentication failed error."""

    def __init__(self, message: str):
        super().__init__(message, 401)


class NotFoundError(APIError):
    """Resource not found error."""

    def __init__(self, message: str):
        super().__init__(message, 404)


class ValidationError(StockAlertError):
    """Validation error."""
    pass


class NetworkError(StockAlertError):
    """Network connection error."""
    pass
