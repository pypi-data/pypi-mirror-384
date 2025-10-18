"""Core configuration manager with auto-save and reload capabilities."""

import hashlib
import threading
from collections.abc import MutableMapping
from pathlib import Path
from typing import Any, Dict, Iterator, Optional, Type

from pydantic import BaseModel

from .exceptions import FileAccessError, ValidationError
from .serializers import get_serializer
from .validators import validate_data


class ConfigManager(MutableMapping):
    """
    A smart configuration manager that auto-saves changes and detects external modifications.

    Features:
    - Auto-save on every write operation
    - Automatic reload when file is modified externally
    - Type validation with Pydantic
    - Thread-safe operations
    - Support for JSON, YAML, and TOML formats

    Example:
        >>> config = ConfigManager("config.yaml")
        >>> config["database"] = {"host": "localhost", "port": 5432}
        >>> print(config["database"]["host"])
        localhost
    """

    def __init__(
            self,
            file_path: str | Path,
            format_: Optional[str] = None,
            auto_save: bool = True,
            auto_reload: bool = True,
            validation_model: Optional[Type[BaseModel]] = None,
            create_if_missing: bool = True,
            validate_on_load: bool = True,
    ):
        """
        Initialize ConfigManager.

        Args:
            file_path: Path to configuration file
            format_: File format (json, yaml, toml). Auto-detected from extension if not specified.
            auto_save: Enable automatic saving on changes
            auto_reload: Enable automatic reloading when file changes
            validation_model: Optional Pydantic model for validation
            create_if_missing: Create file with empty config if it doesn't exist
            validate_on_load: Validate data when loading (set False for empty configs)
        """
        self.file_path = Path(file_path)
        self.auto_save = auto_save
        self.auto_reload = auto_reload
        self.validation_model = validation_model
        self.validate_on_load = validate_on_load

        if format_ is None:
            format_ = self._detect_format_from_extension()

        self.serializer = get_serializer(format_)

        # Thread safety
        self._lock = threading.RLock()

        # Internal state
        self._data: Dict[str, Any] = {}
        self._last_mtime: Optional[float] = None
        self._last_hash: Optional[str] = None

        # Initialize
        if self.file_path.exists():
            self._load()
        elif create_if_missing:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            self._save(skip_validation=True)
        else:
            raise FileAccessError(f"Configuration file not found: {self.file_path}")

    def _detect_format_from_extension(self) -> str:
        """Detect file format from file extension."""
        extension_map = {
            '.json': 'json',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.toml': 'toml',
        }

        extension = self.file_path.suffix.lower()
        if extension in extension_map:
            return extension_map[extension]

        return 'yaml'

    def _load(self) -> None:
        """Load configuration from file."""
        with self._lock:
            try:
                data = self.serializer.load(self.file_path)

                # 如果数据为空且不需要验证，直接使用
                if not data and not self.validate_on_load:
                    self._data = {}
                else:
                    # 只在需要时验证
                    if self.validation_model and self.validate_on_load:
                        validated_data = validate_data(data, self.validation_model)
                        self._data = validated_data
                    else:
                        validated_data = validate_data(data, None)
                        self._data = validated_data

                self._update_file_metadata()
            except ValidationError:
                raise
            except Exception as e:
                raise FileAccessError(f"Failed to load configuration: {e}")

    def _save(self, skip_validation: bool = False) -> None:
        """Save configuration to file."""
        with self._lock:
            try:
                # 可选择跳过验证（用于空配置）
                if not skip_validation:
                    validated_data = validate_data(self._data, self.validation_model)
                else:
                    validated_data = self._data

                self.serializer.dump(validated_data, self.file_path)
                self._update_file_metadata()
            except ValidationError:
                raise
            except Exception as e:
                raise FileAccessError(f"Failed to save configuration: {e}")

    def _update_file_metadata(self) -> None:
        """Update cached file metadata."""
        if self.file_path.exists():
            stat = self.file_path.stat()
            self._last_mtime = stat.st_mtime
            # Only compute hash for small files (< 1MB)
            if stat.st_size < 1024 * 1024:
                with open(self.file_path, "rb") as f:
                    self._last_hash = hashlib.md5(f.read()).hexdigest()
            else:
                self._last_hash = None

    def _check_reload(self) -> None:
        """Check if file was modified and reload if necessary."""
        if not self.auto_reload or not self.file_path.exists():
            return

        with self._lock:
            stat = self.file_path.stat()
            current_mtime = stat.st_mtime

            # Quick check: mtime hasn't changed
            if current_mtime == self._last_mtime:
                return

            # For small files, verify with hash to avoid false positives
            if self._last_hash is not None and stat.st_size < 1024 * 1024:
                with open(self.file_path, "rb") as f:
                    current_hash = hashlib.md5(f.read()).hexdigest()
                if current_hash == self._last_hash:
                    # False alarm, just update mtime
                    self._last_mtime = current_mtime
                    return

            # File actually changed, reload
            self._load()

    # MutableMapping interface

    def __getitem__(self, key: str) -> Any:
        self._check_reload()
        with self._lock:
            return self._data[key]

    def __setitem__(self, key: str, value: Any) -> None:
        with self._lock:
            self._data[key] = value
            if self.auto_save:
                self._save()

    def __delitem__(self, key: str) -> None:
        with self._lock:
            del self._data[key]
            if self.auto_save:
                self._save()

    def __iter__(self) -> Iterator[str]:
        self._check_reload()
        with self._lock:
            return iter(self._data)

    def __len__(self) -> int:
        self._check_reload()
        with self._lock:
            return len(self._data)

    def __repr__(self) -> str:
        return f"ConfigManager({self.file_path}, {len(self._data)} keys)"

    # Additional utility methods

    def reload(self) -> None:
        """Manually reload configuration from file."""
        self._load()

    def save(self) -> None:
        """Manually save configuration to file."""
        self._save()

    def update(self, other: Dict[str, Any]) -> None:  # type: ignore
        """Update configuration with dictionary."""
        with self._lock:
            self._data.update(other)
            if self.auto_save:
                self._save()

    def to_dict(self) -> Dict[str, Any]:
        """Get a copy of the configuration as a dictionary."""
        self._check_reload()
        with self._lock:
            return self._data.copy()

    def clear(self) -> None:
        """Clear all configuration."""
        with self._lock:
            self._data.clear()
            if self.auto_save:
                self._save(skip_validation=True)

    @property
    def format(self) -> str:
        """Get the current file format."""
        # 从序列化器反向查找格式
        format_map = {
            'JSONSerializer': 'json',
            'YAMLSerializer': 'yaml',
            'TOMLSerializer': 'toml',
        }
        serializer_type = type(self.serializer).__name__
        return format_map.get(serializer_type, 'yaml')
