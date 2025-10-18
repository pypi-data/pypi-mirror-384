"""Serialization handlers for different file formats."""

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict

import toml
import yaml

from .exceptions import SerializationError


class Serializer(ABC):
    """Abstract base class for serializers."""

    @abstractmethod
    def load(self, path: Path) -> Dict[str, Any]:
        """Load configuration from file."""
        pass

    @abstractmethod
    def dump(self, data: Dict[str, Any], path: Path) -> None:
        """Save configuration to file."""
        pass


class JSONSerializer(Serializer):
    """JSON serializer with safe defaults."""

    def load(self, path: Path) -> Dict[str, Any]:
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, dict) else {}
        except json.JSONDecodeError as e:
            raise SerializationError(f"Invalid JSON in {path}: {e}")
        except Exception as e:
            raise SerializationError(f"Failed to load JSON from {path}: {e}")

    def dump(self, data: Dict[str, Any], path: Path) -> None:
        try:
            # Atomic write: write to temp file then rename
            temp_path = path.with_suffix(path.suffix + ".tmp")
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False, sort_keys=True)
            temp_path.replace(path)
        except Exception as e:
            raise SerializationError(f"Failed to save JSON to {path}: {e}")


class YAMLSerializer(Serializer):
    """YAML serializer with safe loading."""

    def load(self, path: Path) -> Dict[str, Any]:
        try:
            with open(path, "r", encoding="utf-8") as f:
                # Use safe_load to prevent arbitrary code execution
                data = yaml.safe_load(f)
                return data if isinstance(data, dict) else {}
        except yaml.YAMLError as e:
            raise SerializationError(f"Invalid YAML in {path}: {e}")
        except Exception as e:
            raise SerializationError(f"Failed to load YAML from {path}: {e}")

    def dump(self, data: Dict[str, Any], path: Path) -> None:
        try:
            temp_path = path.with_suffix(path.suffix + ".tmp")
            with open(temp_path, "w", encoding="utf-8") as f:
                yaml.safe_dump(
                    data,
                    f,
                    default_flow_style=False,
                    allow_unicode=True,
                    sort_keys=False,
                )
            temp_path.replace(path)
        except Exception as e:
            raise SerializationError(f"Failed to save YAML to {path}: {e}")


class TOMLSerializer(Serializer):
    """TOML serializer."""

    def load(self, path: Path) -> Dict[str, Any]:
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = toml.load(f)
                return data if isinstance(data, dict) else {}
        except toml.TomlDecodeError as e:
            raise SerializationError(f"Invalid TOML in {path}: {e}")
        except Exception as e:
            raise SerializationError(f"Failed to load TOML from {path}: {e}")

    def dump(self, data: Dict[str, Any], path: Path) -> None:
        try:
            temp_path = path.with_suffix(path.suffix + ".tmp")
            with open(temp_path, "w", encoding="utf-8") as f:
                toml.dump(data, f)
            temp_path.replace(path)
        except Exception as e:
            raise SerializationError(f"Failed to save TOML to {path}: {e}")


# Serializer registry
SERIALIZERS: Dict[str, Serializer] = {
    "json": JSONSerializer(),
    "yaml": YAMLSerializer(),
    "yml": YAMLSerializer(),
    "toml": TOMLSerializer(),
}


def get_serializer(format_name: str) -> Serializer:
    """Get serializer by format name."""
    serializer = SERIALIZERS.get(format_name.lower())
    if not serializer:
        raise ValueError(
            f"Unsupported format: {format_name}. "
            f"Supported formats: {', '.join(SERIALIZERS.keys())}"
        )
    return serializer
