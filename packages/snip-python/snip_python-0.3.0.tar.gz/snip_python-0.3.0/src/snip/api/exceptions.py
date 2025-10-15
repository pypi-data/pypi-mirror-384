"""Custom exceptions raised by the API client."""

from typing import Optional


class AuthenticationException(Exception):
    """An exception raised when an authentication error occurs."""

    details: Optional[dict]

    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message)
        self.details = details

    def __str__(self):
        """Return a string representation of the exception."""
        return f"{super().__str__()} ({self.details})"


class BadRequestException(Exception):
    """An exception raised when the request is invalid."""

    details: Optional[dict]

    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message)
        self.details = details

    def __str__(self):
        """Return a string representation of the exception."""
        return f"{super().__str__()} ({self.details})"
