"""Tests for Configium exceptions."""

import pytest
from configium import ConfigiumError, FileAccessError, SerializationError, ValidationError


def test_configium_error():
    """Test base ConfigiumError exception."""
    # Test basic exception creation
    error = ConfigiumError("Test error message")
    assert str(error) == "Test error message"
    
    # Test exception raising
    with pytest.raises(ConfigiumError) as exc_info:
        raise ConfigiumError("Test error")
    assert str(exc_info.value) == "Test error"


def test_file_access_error():
    """Test FileAccessError exception."""
    error = FileAccessError("File not found")
    assert str(error) == "File not found"
    
    # Verify it inherits from ConfigiumError
    assert isinstance(error, ConfigiumError)
    
    # Test exception raising
    with pytest.raises(FileAccessError) as exc_info:
        raise FileAccessError("Access denied")
    assert str(exc_info.value) == "Access denied"


def test_serialization_error():
    """Test SerializationError exception."""
    error = SerializationError("Invalid JSON format")
    assert str(error) == "Invalid JSON format"
    
    # Verify it inherits from ConfigiumError
    assert isinstance(error, ConfigiumError)
    
    # Test exception raising
    with pytest.raises(SerializationError) as exc_info:
        raise SerializationError("Serialization failed")
    assert str(exc_info.value) == "Serialization failed"


def test_validation_error():
    """Test ValidationError exception."""
    error = ValidationError("Invalid configuration value")
    assert str(error) == "Invalid configuration value"
    
    # Verify it inherits from ConfigiumError
    assert isinstance(error, ConfigiumError)
    
    # Test exception raising
    with pytest.raises(ValidationError) as exc_info:
        raise ValidationError("Validation failed")
    assert str(exc_info.value) == "Validation failed"


def test_exception_inheritance():
    """Test the inheritance hierarchy of exceptions."""
    # All exceptions should inherit from ConfigiumError
    assert issubclass(FileAccessError, ConfigiumError)
    assert issubclass(SerializationError, ConfigiumError)
    assert issubclass(ValidationError, ConfigiumError)
    
    # But they should be distinct classes
    assert FileAccessError is not ConfigiumError
    assert SerializationError is not ConfigiumError
    assert ValidationError is not ConfigiumError


def test_catch_base_exception():
    """Test that base exception can catch derived exceptions."""
    # Catching ConfigiumError should catch all derived exceptions
    with pytest.raises(ConfigiumError):
        raise FileAccessError("File access failed")
    
    with pytest.raises(ConfigiumError):
        raise SerializationError("Serialization failed")
    
    with pytest.raises(ConfigiumError):
        raise ValidationError("Validation failed")


def test_exception_with_complex_message():
    """Test exceptions with complex messages."""
    complex_msg = "Error with multiple lines\nand special characters: !@#$%^&*()"
    error = ValidationError(complex_msg)
    assert complex_msg in str(error)
    
    long_msg = "A" * 1000  # Very long message
    error = SerializationError(long_msg)
    assert str(error) == long_msg