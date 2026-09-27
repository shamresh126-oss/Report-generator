"""Custom exceptions for the Enterprise Business Report Generator.

Defines a hierarchy of domain-specific exceptions to enable granular error
handling, informative CLI error reporting, and detailed diagnostic logging.
"""

from typing import Optional


class ReportGeneratorError(Exception):
    """Base exception class for all Report Generator application errors."""

    def __init__(self, message: str, original_exception: Optional[Exception] = None) -> None:
        super().__init__(message)
        self.message = message
        self.original_exception = original_exception

    def __str__(self) -> str:
        return self.message


class ConfigurationError(ReportGeneratorError):
    """Raised when there is an error in environment configuration or file paths."""
    pass


class APIClientError(ReportGeneratorError):
    """Raised when an API request fails due to connection, HTTP, or data errors."""
    pass


class DataProcessingError(ReportGeneratorError):
    """Raised when input data is missing, invalid, or cannot be processed."""
    pass


class PDFGenerationError(ReportGeneratorError):
    """Raised when ReportLab fails to construct or save the PDF document."""
    pass
