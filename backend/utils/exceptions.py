"""Custom exceptions for the Digital Forensics Triage Tool."""

from typing import Optional


class DFTError(Exception):
    """Base exception class for all DFT-Tool errors."""

    def __init__(self, message: str, details: Optional[dict] = None):
        """
        Initialize the exception.

        Args:
            message: Error message
            details: Optional dictionary with additional error details
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ConfigurationError(DFTError):
    """Raised when there's an error in the configuration."""

    pass


class ValidationError(DFTError):
    """Raised when input validation fails."""

    pass


class FileSystemError(DFTError):
    """Raised when file system operations fail."""

    pass


class SecurityError(DFTError):
    """Raised when a security check fails."""

    pass


class ProcessingError(DFTError):
    """Raised when file processing fails."""

    pass


class ConcurrencyError(DFTError):
    """Raised when there's an error in parallel processing."""

    pass
