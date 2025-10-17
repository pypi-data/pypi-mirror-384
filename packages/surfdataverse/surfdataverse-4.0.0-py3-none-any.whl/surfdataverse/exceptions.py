"""
Custom exceptions for the SurfDataverse package.
"""


class SurfDataverseError(Exception):
    """Base exception for all SurfDataverse errors."""

    pass


class AuthenticationError(SurfDataverseError):
    """Raised when authentication fails."""

    pass


class ConnectionError(SurfDataverseError):
    """Raised when connection to Dataverse fails."""

    pass


class ConfigurationError(SurfDataverseError):
    """Raised when configuration is invalid or missing."""

    pass


class DataverseAPIError(SurfDataverseError):
    """Raised when Dataverse API returns an error."""

    def __init__(self, message, status_code=None, response_text=None):
        super().__init__(message)
        self.status_code = status_code
        self.response_text = response_text


class EntityError(SurfDataverseError):
    """Raised when entity operations fail."""

    pass


class ValidationError(SurfDataverseError):
    """Raised when data validation fails."""

    pass
