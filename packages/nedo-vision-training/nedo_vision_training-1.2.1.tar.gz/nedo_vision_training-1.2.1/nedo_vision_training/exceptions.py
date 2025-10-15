"""
Custom exceptions for the Nedo Vision Training Service Library.
"""

class TrainingServiceError(Exception):
    """Base exception for training service errors."""
    pass


class ConfigurationError(TrainingServiceError):
    """Raised when there's a configuration error."""
    pass


class AuthenticationError(TrainingServiceError):
    """Raised when authentication fails."""
    pass


class ConnectionError(TrainingServiceError):
    """Raised when connection to services fails."""
    pass


class GrpcClientError(TrainingServiceError):
    """Raised when gRPC client operations fail."""
    pass 