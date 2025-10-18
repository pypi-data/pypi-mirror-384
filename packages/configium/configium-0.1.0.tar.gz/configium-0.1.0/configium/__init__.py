"""Configium - A smart configuration manager with auto-save and type validation."""

__version__ = "0.1.0"

from .exceptions import (
    ConfigiumError,
    FileAccessError,
    SerializationError,
    ValidationError,
)
from .manager import ConfigManager

__all__ = [
    "ConfigManager",
    "ConfigiumError",
    "FileAccessError",
    "SerializationError",
    "ValidationError",
]
