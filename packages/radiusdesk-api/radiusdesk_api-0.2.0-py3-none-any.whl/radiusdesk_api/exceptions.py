"""Custom exceptions for the RadiusDesk API client."""


class RadiusDeskError(Exception):
    """Base exception for all RadiusDesk API errors."""
    pass


class AuthenticationError(RadiusDeskError):
    """Raised when authentication fails."""
    pass


class TokenExpiredError(RadiusDeskError):
    """Raised when the authentication token has expired."""
    pass


class APIError(RadiusDeskError):
    """Raised when an API request fails."""

    def __init__(self, message: str, status_code: int = None, response_data: dict = None):
        """
        Initialize APIError.

        Args:
            message: Error message
            status_code: HTTP status code
            response_data: Response data from the API
        """
        self.status_code = status_code
        self.response_data = response_data
        super().__init__(message)


class ValidationError(RadiusDeskError):
    """Raised when input validation fails."""
    pass


class ResourceNotFoundError(RadiusDeskError):
    """Raised when a requested resource is not found."""
    pass
