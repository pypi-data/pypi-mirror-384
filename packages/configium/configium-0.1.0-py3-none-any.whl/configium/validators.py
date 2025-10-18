"""Validation utilities using Pydantic."""

from typing import Any, Dict, Optional, Type

from pydantic import BaseModel, ValidationError as PydanticValidationError

from .exceptions import ValidationError


def validate_data(
        data: Dict[str, Any],
        model: Optional[Type[BaseModel]] = None,
        allow_partial: bool = False,
) -> Dict[str, Any]:
    """
    Validate configuration data.

    Args:
        data: Configuration dictionary to validate
        model: Optional Pydantic model for strict validation
        allow_partial: Allow partial data (missing required fields)

    Returns:
        Validated data dictionary

    Raises:
        ValidationError: If validation fails
    """
    if model is None:
        # Basic type validation - ensure all values are JSON-serializable
        try:
            _validate_json_serializable(data)
            return data
        except Exception as e:
            raise ValidationError(f"Configuration contains non-serializable data: {e}")

    if not data and allow_partial:
        return data

    # Strict validation with Pydantic model
    try:
        validated = model(**data)
        return validated.model_dump()
    except PydanticValidationError as e:
        error_details = []
        for error in e.errors():
            field = ".".join(str(x) for x in error["loc"])
            msg = error["msg"]
            error_details.append(f"  - {field}: {msg}")

        error_msg = "Configuration validation failed:\n" + "\n".join(error_details)
        raise ValidationError(error_msg)


def _validate_json_serializable(obj: Any, path: str = "root") -> None:
    """Recursively check if object is JSON-serializable."""
    if obj is None or isinstance(obj, (bool, int, float, str)):
        return

    if isinstance(obj, dict):
        for key, value in obj.items():
            if not isinstance(key, str):
                raise ValueError(f"Non-string key at {path}.{key}")
            _validate_json_serializable(value, f"{path}.{key}")

    elif isinstance(obj, (list, tuple)):
        for i, item in enumerate(obj):
            _validate_json_serializable(item, f"{path}[{i}]")

    else:
        raise ValueError(f"Non-serializable type {type(obj).__name__} at {path}")
