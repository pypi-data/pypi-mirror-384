"""Tests for ConfigManager."""

import json
import time

import pytest
import toml
import yaml
from pydantic import BaseModel

from configium import ConfigManager, ValidationError


def test_basic_operations(temp_config_file):
    """Test basic dict operations."""
    config = ConfigManager(temp_config_file)

    # Set values
    config["name"] = "test"
    config["count"] = 42

    # Get values
    assert config["name"] == "test"
    assert config["count"] == 42

    # Length
    assert len(config) == 2

    # Iteration
    assert set(config.keys()) == {"name", "count"}

    # Delete
    del config["count"]
    assert "count" not in config


def test_auto_save(temp_config_file):
    """Test automatic saving."""
    config = ConfigManager(temp_config_file)
    config["key"] = "value"

    # Create new instance and verify data persisted
    config2 = ConfigManager(temp_config_file)
    assert config2["key"] == "value"


def test_auto_reload(temp_config_file):
    """Test automatic reloading."""
    config = ConfigManager(temp_config_file)
    config["original"] = "value"

    # Modify file externally
    time.sleep(0.01)  # Ensure mtime changes
    with open(temp_config_file, "w") as f:
        yaml.safe_dump({"external": "change"}, f)

    # Access should trigger reload
    assert "external" in config
    assert config["external"] == "change"


def test_nested_dict(temp_config_file):
    """Test nested dictionary support."""
    config = ConfigManager(temp_config_file)
    config["database"] = {
        "host": "localhost",
        "port": 5432,
        "credentials": {
            "user": "admin",
            "password": "secret"
        }
    }

    assert config["database"]["host"] == "localhost"
    assert config["database"]["credentials"]["user"] == "admin"


def test_json_format(tmp_path):
    """Test JSON format."""
    json_file = tmp_path / "config.json"
    config = ConfigManager(json_file)  
    config["test"] = "json"

    
    with open(json_file, "r") as f:
        content = json.load(f)
    assert content["test"] == "json"

    config2 = ConfigManager(json_file)
    assert config2["test"] == "json"
    assert config2.format == "json"  


def test_toml_format(tmp_path):
    """Test TOML format."""
    toml_file = tmp_path / "config.toml"
    config = ConfigManager(toml_file)  
    config["test"] = "toml"

    
    with open(toml_file, "r") as f:
        content = toml.load(f)
    assert content["test"] == "toml"

    config2 = ConfigManager(toml_file)
    assert config2["test"] == "toml"
    assert config2.format == "toml"  


def test_yaml_format(tmp_path):
    """Test YAML format."""
    yaml_file = tmp_path / "config.yaml"
    config = ConfigManager(yaml_file)  
    config["test"] = "yaml"

    
    with open(yaml_file, "r") as f:
        content = yaml.safe_load(f)
    assert content["test"] == "yaml"

    config2 = ConfigManager(yaml_file)
    assert config2["test"] == "yaml"
    assert config2.format == "yaml"  


def test_yaml_yml_extension(tmp_path):
    """Test .yml extension detection."""
    yml_file = tmp_path / "config.yml"
    config = ConfigManager(yml_file)  
    config["test"] = "yaml"

    
    with open(yml_file, "r") as f:
        content = yaml.safe_load(f)
    assert content["test"] == "yaml"

    config2 = ConfigManager(yml_file)
    assert config2["test"] == "yaml"
    assert config2.format == "yaml"  


def test_explicit_format_override(tmp_path):
    """Test explicit format override."""
    
    no_ext_file = tmp_path / "config"

    # 显式指定 JSON 格式
    config = ConfigManager(no_ext_file, format_="json")
    config["test"] = "json"

    # 验证文件确实是 JSON 格式
    with open(no_ext_file, "r") as f:
        content = json.load(f)
    assert content["test"] == "json"
    assert config.format == "json"


def test_default_format_no_extension(tmp_path):
    """Test default format for files without extension."""
    
    no_ext_file = tmp_path / "config"

    # 不指定格式，应该使用默认的 yaml
    config = ConfigManager(no_ext_file)
    config["test"] = "default_yaml"

    # 验证文件确实是 YAML 格式（默认）
    with open(no_ext_file, "r") as f:
        content = yaml.safe_load(f)
    assert content["test"] == "default_yaml"
    assert config.format == "yaml"


def test_pydantic_validation(temp_config_file):
    """Test Pydantic model validation."""

    class ConfigModel(BaseModel):
        name: str
        count: int

    # 方式1：创建时不验证空配置
    config = ConfigManager(
        temp_config_file,
        validation_model=ConfigModel,
        validate_on_load=False  # 允许空配置
    )

    # Valid data
    config.update({"name": "test", "count": 42})
    assert config["name"] == "test"

    # Invalid data should raise error
    with pytest.raises(ValidationError):
        config["count"] = "not a number"


def test_pydantic_validation_with_existing_data(tmp_path):
    """Test Pydantic validation with pre-existing valid data."""

    class ConfigModel(BaseModel):
        name: str
        count: int

    config_file = tmp_path / "config.yaml"

    # 先创建有效的配置文件
    with open(config_file, "w") as f:
        yaml.safe_dump({"name": "test", "count": 42}, f)

    # 现在可以正常加载和验证
    config = ConfigManager(config_file, validation_model=ConfigModel)
    assert config["name"] == "test"
    assert config["count"] == 42

    # 修改为无效数据应该失败
    with pytest.raises(ValidationError):
        config["count"] = "invalid"


def test_pydantic_optional_fields(temp_config_file):
    """Test Pydantic with optional fields."""

    from typing import Optional

    class ConfigModel(BaseModel):
        name: str
        count: Optional[int] = None  # 可选字段

    # 使用可选字段的模型
    config = ConfigManager(
        temp_config_file,
        validation_model=ConfigModel,
        validate_on_load=False
    )

    # 只设置必需字段
    config["name"] = "test"
    assert config["name"] == "test"
    assert "count" not in config or config.get("count") is None


def test_thread_safety(temp_config_file):
    """Test thread-safe operations."""
    import threading

    config = ConfigManager(temp_config_file)
    errors = []

    def writer(key, value):
        try:
            for i in range(100):
                config[f"{key}_{i}"] = value
        except Exception as e:
            errors.append(e)

    threads = [
        threading.Thread(target=writer, args=(f"thread{i}", i))
        for i in range(5)
    ]

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(errors) == 0
    assert len(config) == 500


def test_update_method(temp_config_file):
    """Test update method."""
    config = ConfigManager(temp_config_file)
    config.update({
        "key1": "value1",
        "key2": "value2",
    })

    assert config["key1"] == "value1"
    assert config["key2"] == "value2"


def test_to_dict(temp_config_file):
    """Test to_dict method."""
    config = ConfigManager(temp_config_file)
    config["test"] = "value"

    data = config.to_dict()
    assert isinstance(data, dict)
    assert data["test"] == "value"

    # Ensure it's a copy
    data["test"] = "modified"
    assert config["test"] == "value"


def test_validation_error_message(temp_config_file):
    """Test that validation errors are informative."""

    class StrictModel(BaseModel):
        name: str
        age: int
        email: str

    config = ConfigManager(
        temp_config_file,
        validation_model=StrictModel,
        validate_on_load=False
    )

    # Try to save incomplete data
    with pytest.raises(ValidationError) as exc_info:
        config.update({"name": "John"})  # Missing age and email

    # Check error message is informative
    error_msg = str(exc_info.value)
    assert "age" in error_msg.lower()
    assert "email" in error_msg.lower()
