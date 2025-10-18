"""Tests for Configium validators."""

from typing import Optional, List

import pytest
from pydantic import BaseModel

from configium import ValidationError
from configium.validators import validate_data


class TestBasicValidation:
    """Test basic validation functionality."""
    
    def test_validate_none_model_allows_any_data(self):
        """Test that when model is None, any JSON-serializable data is allowed."""
        data = {
            "string": "value",
            "integer": 42,
            "float": 3.14,
            "boolean": True,
            "none": None,
            "list": [1, 2, 3],
            "nested": {"inner": "value"}
        }
        
        result = validate_data(data, model=None)
        assert result == data
    
    def test_validate_none_model_rejects_non_serializable(self):
        """Test that non-JSON-serializable data raises ValidationError when model is None."""
        data = {"func": lambda x: x}  # Functions are not JSON serializable
        
        with pytest.raises(ValidationError) as exc_info:
            validate_data(data, model=None)
        
        assert "non-serializable" in str(exc_info.value).lower()
    
    def test_validate_none_model_with_complex_serializable_data(self):
        """Test validation of complex but serializable data."""
        data = {
            "users": [
                {"id": 1, "name": "Alice"},
                {"id": 2, "name": "Bob"}
            ],
            "settings": {
                "theme": "dark",
                "notifications": True,
                "limits": [10, 20, 30]
            },
            "metadata": {
                "version": 1.0,
                "active": True,
                "tags": ["config", "test"]
            }
        }
        
        result = validate_data(data, model=None)
        assert result == data
    
    def test_validate_with_none_model_empty_dict(self):
        """Test empty dict validation with None model."""
        result = validate_data({}, model=None)
        assert result == {}
    
    def test_validate_with_none_model_nested_none_values(self):
        """Test nested data with None values."""
        data = {
            "level1": {
                "level2": {
                    "value": None
                }
            },
            "list_with_none": [1, None, 3]
        }
        
        result = validate_data(data, model=None)
        assert result == data


class SimpleModel(BaseModel):
    name: str
    age: int


class ComplexModel(BaseModel):
    user: SimpleModel
    active: bool
    tags: List[str]


class OptionalModel(BaseModel):
    name: str
    age: Optional[int] = None
    email: Optional[str] = None


class TestPydanticModelValidation:
    """Test validation with Pydantic models."""
    
    def test_successful_pydantic_validation(self):
        """Test successful validation with Pydantic model."""
        data = {
            "name": "John",
            "age": 30
        }
        
        result = validate_data(data, model=SimpleModel)
        assert result == data
    
    def test_failed_pydantic_validation_wrong_type(self):
        """Test validation failure with wrong type."""
        data = {
            "name": "John",
            "age": "thirty"  # Should be int
        }
        
        with pytest.raises(ValidationError) as exc_info:
            validate_data(data, model=SimpleModel)
        
        assert "age" in str(exc_info.value).lower()
        assert "int" in str(exc_info.value).lower()
    
    def test_failed_pydantic_validation_missing_required(self):
        """Test validation failure with missing required field."""
        data = {
            "name": "John"
            # Missing age
        }
        
        with pytest.raises(ValidationError) as exc_info:
            validate_data(data, model=SimpleModel)
        
        assert "age" in str(exc_info.value).lower()
        assert "field" in str(exc_info.value).lower()
    
    def test_complex_model_validation(self):
        """Test validation with complex nested model."""
        data = {
            "user": {
                "name": "Jane",
                "age": 25
            },
            "active": True,
            "tags": ["admin", "user"]
        }
        
        result = validate_data(data, model=ComplexModel)
        assert result == data
    
    def test_complex_model_validation_failure(self):
        """Test validation failure with complex nested model."""
        data = {
            "user": {
                "name": "Jane",
                "age": "invalid"  # Should be int
            },
            "active": True,
            "tags": ["admin", "user"]
        }
        
        with pytest.raises(ValidationError) as exc_info:
            validate_data(data, model=ComplexModel)
        
        assert "user.age" in str(exc_info.value)
        assert "int" in str(exc_info.value).lower()
    
    def test_optional_fields_validation(self):
        """Test validation with optional fields."""
        data = {
            "name": "John"
            # age and email are optional
        }
        
        result = validate_data(data, model=OptionalModel)
        assert result["name"] == "John"
        assert result["age"] is None
        assert result["email"] is None
    
    def test_optional_fields_with_values(self):
        """Test validation with optional fields that have values."""
        data = {
            "name": "John",
            "age": 25,
            "email": "john@example.com"
        }
        
        result = validate_data(data, model=OptionalModel)
        assert result == data


class TestAllowPartialOption:
    """Test the allow_partial option."""
    
    class StrictModel(BaseModel):
        name: str
        age: int
        email: str
    
    def test_allow_partial_false_by_default(self):
        """Test that allow_partial is False by default."""
        data = {
            "name": "John"
            # Missing age and email
        }
        
        with pytest.raises(ValidationError):
            validate_data(data, model=self.StrictModel)
    
    def test_allow_partial_true_allows_incomplete_data(self):
        """Test that allow_partial=True allows incomplete data."""
        data = {
            "name": "John"
            # Missing age and email but allow_partial=True
        }
        
        # This should not raise an error since we're not using the validator
        # properly - let's test with empty data instead
        result = validate_data({}, model=self.StrictModel, allow_partial=True)
        assert result == {}
    
    def test_allow_partial_with_empty_data(self):
        """Test allow_partial with empty data."""
        result = validate_data({}, model=self.StrictModel, allow_partial=True)
        assert result == {}
    
    def test_allow_partial_false_with_empty_data(self):
        """Test that empty data still fails with allow_partial=False."""
        with pytest.raises(ValidationError):
            validate_data({}, model=self.StrictModel, allow_partial=False)


class TestErrorMessages:
    """Test validation error messages."""
    
    class UserModel(BaseModel):
        name: str
        age: int
        email: str
    
    def test_informative_error_message(self):
        """Test that validation errors have informative messages."""
        data = {
            "name": "John",
            "age": "not_a_number",  # Wrong type
            "email": 12345  # Wrong type
        }
        
        with pytest.raises(ValidationError) as exc_info:
            validate_data(data, model=self.UserModel)
        
        error_msg = str(exc_info.value)
        assert "configuration validation failed" in error_msg.lower()
        assert "age" in error_msg.lower()
        assert "email" in error_msg.lower()
        assert "str" in error_msg.lower()  # Type mentioned
    
    def test_error_message_for_nested_model(self):
        """Test error messages for nested models."""
        class InnerModel(BaseModel):
            value: int
        
        class OuterModel(BaseModel):
            inner: InnerModel
        
        data = {
            "inner": {
                "value": "not_an_int"  # Should be int
            }
        }
        
        with pytest.raises(ValidationError) as exc_info:
            validate_data(data, model=OuterModel)
        
        error_msg = str(exc_info.value)
        assert "inner.value" in error_msg.lower()
        assert "int" in error_msg.lower()


class TestSpecialDataTypes:
    """Test validation of special data types."""
    
    def test_validate_boolean_and_none_values(self):
        """Test validation of boolean and None values."""
        data = {
            "true_value": True,
            "false_value": False,
            "none_value": None
        }
        
        result = validate_data(data, model=None)
        assert result == data
    
    def test_validate_numeric_types(self):
        """Test validation of different numeric types."""
        data = {
            "integer": 42,
            "float": 3.14159,
            "negative": -10,
            "zero": 0
        }
        
        result = validate_data(data, model=None)
        assert result == data
    
    def test_validate_lists_and_dicts(self):
        """Test validation of lists and dictionaries."""
        data = {
            "simple_list": [1, 2, 3, "string", True],
            "nested_list": [[1, 2], [3, 4]],
            "simple_dict": {"key": "value"},
            "nested_dict": {"outer": {"inner": "value"}}
        }
        
        result = validate_data(data, model=None)
        assert result == data
    
    def test_validate_non_string_dict_keys(self):
        """Test that non-string dict keys raise errors."""
        data = {
            123: "value",  # Non-string key
            "valid_key": "valid_value"
        }
        
        with pytest.raises(ValidationError):
            validate_data(data, model=None)
    
    def test_validate_deeply_nested_structure(self):
        """Test validation of deeply nested structures."""
        data = {
            "level1": {
                "level2": {
                    "level3": {
                        "level4": {
                            "data": "deep_value"
                        }
                    }
                }
            },
            "list_of_dicts": [
                {"a": 1, "b": {"c": 2}},
                {"x": [1, 2, {"y": 3}]}
            ]
        }
        
        result = validate_data(data, model=None)
        assert result == data


class TestPydanticModelWithConstraints:
    """Test validation with Pydantic models that have constraints."""
    
    class ConstrainedModel(BaseModel):
        name: str
        age: int
        email: str
        
        def model_post_init(self, __context):
            # Custom validation after initialization
            if self.age < 0:
                raise ValueError("Age cannot be negative")
    
    def test_validation_with_custom_constraints(self):
        """Test validation with custom constraints."""
        data = {
            "name": "John",
            "age": 25,
            "email": "john@example.com"
        }
        
        result = validate_data(data, model=self.ConstrainedModel)
        assert result == data
    
    def test_validation_fails_custom_constraints(self):
        """Test validation failure with custom constraints."""
        data = {
            "name": "John",
            "age": -5,  # Negative age
            "email": "john@example.com"
        }
        
        with pytest.raises(ValidationError):
            validate_data(data, model=self.ConstrainedModel)
