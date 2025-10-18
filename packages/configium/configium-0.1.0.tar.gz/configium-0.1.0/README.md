# Configium 🔧

A smart, type-safe configuration manager for Python with auto-save and auto-reload capabilities.

## Features

✨ **Auto-save**: Changes are automatically persisted to disk  
🔄 **Auto-reload**: Detects external file modifications and reloads  
🛡️ **Type-safe**: Pydantic integration for robust validation  
📝 **Multiple formats**: Support for JSON, YAML, and TOML  
🔒 **Thread-safe**: Safe for concurrent access  
⚡ **High performance**: Efficient file change detection  

## Installation

```bash
pip install configium
```

## Quick Start

```python
from configium import ConfigManager

# Create or load configuration
config = ConfigManager("config.yaml")

# Use it like a dictionary
config["database"] = {
    "host": "localhost",
    "port": 5432
}

# Changes are automatically saved!
print(config["database"]["host"])  # localhost

# Nested access
config["api"]["key"] = "secret"
```

## Advanced Usage

### Type Validation with Pydantic

```python
from pydantic import BaseModel
from configium import ConfigManager

class DatabaseConfig(BaseModel):
    host: str
    port: int
    username: str

config = ConfigManager("config.yaml", validation_model=DatabaseConfig)

# This works
config.update({"host": "localhost", "port": 5432, "username": "admin"})

# This raises ValidationError
config["port"] = "invalid"  # ❌ Must be int
```

### Different Formats

```python
# JSON
config = ConfigManager("config.json", format="json")

# TOML
config = ConfigManager("config.toml", format="toml")

# Auto-detect from extension
config = ConfigManager("config.yaml")  # Automatically uses YAML
```

### Manual Control

```python
# Disable auto-save
config = ConfigManager("config.yaml", auto_save=False)
config["key"] = "value"
config.save()  # Manually save

# Disable auto-reload
config = ConfigManager("config.yaml", auto_reload=False)
config.reload()  # Manually reload
```

### Thread-Safe Operations

```python
from threading import Thread

config = ConfigManager("config.yaml")

def update_config(key, value):
    config[key] = value

# Safe concurrent access
threads = [Thread(target=update_config, args=(f"key{i}", i)) for i in range(10)]
for t in threads:
    t.start()
for t in threads:
    t.join()
```

## API Reference

### ConfigManager

```python
ConfigManager(
    file_path: str | Path,
    format: str = "yaml",
    auto_save: bool = True,
    auto_reload: bool = True,
    validation_model: Optional[Type[BaseModel]] = None,
    create_if_missing: bool = True,
)
```

**Parameters:**
- `file_path`: Path to configuration file
- `format`: File format (json, yaml, toml)
- `auto_save`: Enable automatic saving
- `auto_reload`: Enable automatic reloading
- `validation_model`: Pydantic model for validation
- `create_if_missing`: Create file if it doesn't exist

**Methods:**
- `reload()`: Manually reload from file
- `save()`: Manually save to file
- `update(dict)`: Update multiple values
- `to_dict()`: Get configuration as dictionary
- `clear()`: Clear all configuration

## Performance

Configium is designed for high performance:

- **Smart change detection**: Uses mtime + hash for accurate detection
- **Atomic writes**: Prevents corruption during saves
- **Minimal overhead**: Dict proxy with negligible performance impact
- **Efficient locking**: Fine-grained locks for thread safety

## Security

- ✅ Uses `yaml.safe_load()` to prevent code execution
- ✅ Atomic file writes prevent corruption
- ✅ Type validation prevents injection attacks
- ✅ No eval() or exec() usage

## Contributing

Contributions welcome! Please check out our [GitHub repository](https://github.com/Konecos/configium).

## License

MIT License - see LICENSE file for details.
