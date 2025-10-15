"""
Custom exceptions for the VRIN SDK
"""


class VRINError(Exception):
    """Base exception for all VRIN SDK errors."""
    pass


class JobFailedError(VRINError):
    """Raised when a job fails during processing."""
    pass


class TimeoutError(VRINError):
    """Raised when an operation times out."""
    pass


class AuthenticationError(VRINError):
    """Raised when authentication fails."""
    pass


class RateLimitError(VRINError):
    """Raised when rate limits are exceeded."""
    pass


class ValidationError(VRINError):
    """Raised when input validation fails."""
    pass


class ServiceUnavailableError(VRINError):
    """Raised when the VRIN service is unavailable."""
    pass 