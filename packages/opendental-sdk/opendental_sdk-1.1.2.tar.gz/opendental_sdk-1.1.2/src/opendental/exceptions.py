"""Exceptions for Open Dental SDK."""

from typing import Optional, Dict


class OpenDentalAPIError(Exception):
    """Exception raised for Open Dental API errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_data: Optional[Dict] = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data or {}


class OpenDentalValidationError(OpenDentalAPIError):
    """Exception raised for validation errors."""
    pass


class OpenDentalAuthenticationError(OpenDentalAPIError):
    """Exception raised for authentication errors."""
    pass


class OpenDentalNotFoundError(OpenDentalAPIError):
    """Exception raised when a resource is not found."""
    pass