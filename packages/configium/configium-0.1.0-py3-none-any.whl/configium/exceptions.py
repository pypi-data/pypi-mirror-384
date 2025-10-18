"""Custom exceptions for Configium."""


class ConfigiumError(Exception):
    """Base exception for all Configium errors."""
    pass


class SerializationError(ConfigiumError):
    """Raised when serialization/deserialization fails."""
    pass


class ValidationError(ConfigiumError):
    """Raised when configuration validation fails."""
    pass


class FileAccessError(ConfigiumError):
    """Raised when file operations fail."""
    pass