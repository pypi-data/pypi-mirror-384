"""Module to hold all custom exceptions for the package."""
from typing import Optional


class NoVerificationElement(Exception):
    """Raised when no verification element is set for the page."""

    pass


class BadRequestError(Exception):
    """Exception for a bad request in t_requests."""

    def __init__(self, message: str, exception: Optional[Exception] = None) -> None:
        """Initialize the exception with a message and an exception.

        Args:
            message (str): The message to display.
            exception (Exception, optional): The exception that was raised. Defaults to None.
        """
        super().__init__(message)
        self.raised_exception = exception


class NoURL(Exception):
    """Raised when no URL is set for the page."""

    pass
