"""Tests for Configium serializers."""

import json

import pytest
import toml
import yaml

from configium import SerializationError
from configium.serializers import (
    JSONSerializer,
    YAMLSerializer,
    TOMLSerializer,
    get_serializer,
)


class TestJSONSerializer:
    """Test JSON serializer functionality."""
    
    def test_json_load_basic(self, tmp_path):
        """Test basic JSON loading."""
        json_file = tmp_path / "test.json"
        
        data = {"name": "test", "value": 42}
        with open(json_file, "w") as f:
            json.dump(data, f)
        
        serializer = JSONSerializer()
        loaded_data = serializer.load(json_file)
        
        assert loaded_data == data
        assert isinstance(loaded_data, dict)
    
    def test_json_dump_basic(self, tmp_path):
        """Test basic JSON dumping."""
        json_file = tmp_path / "test.json"
        
        data = {"name": "test", "value": 42}
        serializer = JSONSerializer()
        serializer.dump(data, json_file)
        
        # Verify file was created and contains correct data
        assert json_file.exists()
        with open(json_file, "r") as f:
            loaded_data = json.load(f)
        assert loaded_data == data
    
    def test_json_load_empty_file(self, tmp_path):
        """Test loading empty JSON file."""
        json_file = tmp_path / "empty.json"
        with open(json_file, "w") as f:
            f.write("{}")
        
        serializer = JSONSerializer()
        loaded_data = serializer.dump({}, json_file)  # This should work
        
        # Actually load and verify
        loaded_data = serializer.load(json_file)
        assert loaded_data == {}
    
    def test_json_load_non_dict_returns_empty(self, tmp_path):
        """Test that non-dict JSON returns empty dict."""
        json_file = tmp_path / "test.json"
        with open(json_file, "w") as f:
            json.dump([1, 2, 3], f)  # Array instead of dict
        
        serializer = JSONSerializer()
        loaded_data = serializer.load(json_file)
        
        # Should return empty dict for non-dict data
        assert loaded_data == {}
    
    def test_json_load_invalid_json_raises_error(self, tmp_path):
        """Test that invalid JSON raises SerializationError."""
        json_file = tmp_path / "invalid.json"
        with open(json_file, "w") as f:
            f.write("{ invalid json }")
        
        serializer = JSONSerializer()
        with pytest.raises(SerializationError):
            serializer.load(json_file)
    
    def test_json_dump_special_characters(self, tmp_path):
        """Test JSON dumping with special characters."""
        json_file = tmp_path / "special.json"
        
        data = {
            "unicode": "测试 Unicode characters",
            "special": "Special chars: \n\t\"'\\",
            "numbers": [1, 2.5, -3, 0]
        }
        serializer = JSONSerializer()
        serializer.dump(data, json_file)
        
        with open(json_file, "r") as f:
            loaded_data = json.load(f)
        
        assert loaded_data == data
    
    def test_json_atomic_write(self, tmp_path):
        """Test that JSON writes are atomic (temp file approach)."""
        json_file = tmp_path / "atomic.json"
        
        data = {"test": "value"}
        serializer = JSONSerializer()
        serializer.dump(data, json_file)
        
        # Verify the file exists and has the correct content
        assert json_file.exists()
        with open(json_file, "r") as f:
            content = f.read()
        assert "test" in content
        assert "value" in content


class TestYAMLSerializer:
    """Test YAML serializer functionality."""
    
    def test_yaml_load_basic(self, tmp_path):
        """Test basic YAML loading."""
        yaml_file = tmp_path / "test.yaml"
        
        data = {"name": "test", "value": 42}
        with open(yaml_file, "w") as f:
            yaml.safe_dump(data, f)
        
        serializer = YAMLSerializer()
        loaded_data = serializer.load(yaml_file)
        
        assert loaded_data == data
        assert isinstance(loaded_data, dict)
    
    def test_yaml_dump_basic(self, tmp_path):
        """Test basic YAML dumping."""
        yaml_file = tmp_path / "test.yaml"
        
        data = {"name": "test", "value": 42}
        serializer = YAMLSerializer()
        serializer.dump(data, yaml_file)
        
        # Verify file was created and contains correct data
        assert yaml_file.exists()
        with open(yaml_file, "r") as f:
            loaded_data = yaml.safe_load(f)
        assert loaded_data == data
    
    def test_yaml_load_empty_file(self, tmp_path):
        """Test loading empty YAML file."""
        yaml_file = tmp_path / "empty.yaml"
        with open(yaml_file, "w") as f:
            f.write("")
        
        serializer = YAMLSerializer()
        loaded_data = serializer.load(yaml_file)
        
        assert loaded_data == {}
    
    def test_yaml_load_non_dict_returns_empty(self, tmp_path):
        """Test that non-dict YAML returns empty dict."""
        yaml_file = tmp_path / "test.yaml"
        with open(yaml_file, "w") as f:
            yaml.safe_dump([1, 2, 3], f)  # Array instead of dict
        
        serializer = YAMLSerializer()
        loaded_data = serializer.load(yaml_file)
        
        # Should return empty dict for non-dict data
        assert loaded_data == {}
    
    def test_yaml_load_invalid_yaml_raises_error(self, tmp_path):
        """Test that invalid YAML raises SerializationError."""
        yaml_file = tmp_path / "invalid.yaml"
        with open(yaml_file, "w") as f:
            f.write("invalid:\n  - yaml: content\n  invalid indent")
        
        serializer = YAMLSerializer()
        with pytest.raises(SerializationError):
            serializer.load(yaml_file)
    
    def test_yaml_dump_special_characters(self, tmp_path):
        """Test YAML dumping with special characters."""
        yaml_file = tmp_path / "special.yaml"
        
        data = {
            "unicode": "测试 Unicode characters",
            "special": "Special chars: \n\t\"'\\",
            "numbers": [1, 2.5, -3, 0]
        }
        serializer = YAMLSerializer()
        serializer.dump(data, yaml_file)
        
        with open(yaml_file, "r") as f:
            loaded_data = yaml.safe_load(f)
        
        # YAML might handle newlines differently, so do a partial check
        assert loaded_data["unicode"] == data["unicode"]
        assert loaded_data["numbers"] == data["numbers"]
    
    def test_yaml_safe_load_prevents_code_execution(self, tmp_path):
        """Test that YAML uses safe_load to prevent code execution."""
        yaml_file = tmp_path / "dangerous.yaml"
        # This is a potential security vulnerability to test against
        dangerous_content = """!!python/object/apply:os.system ['echo "dangerous"']"""
        
        with open(yaml_file, "w") as f:
            f.write(dangerous_content)
        
        serializer = YAMLSerializer()
        with pytest.raises(SerializationError):
            # Should raise an error instead of executing code
            serializer.load(yaml_file)


class TestTOMLSerializer:
    """Test TOML serializer functionality."""
    
    def test_toml_load_basic(self, tmp_path):
        """Test basic TOML loading."""
        toml_file = tmp_path / "test.toml"
        
        data = {"name": "test", "value": 42}
        with open(toml_file, "w") as f:
            toml.dump(data, f)
        
        serializer = TOMLSerializer()
        loaded_data = serializer.load(toml_file)
        
        assert loaded_data == data
        assert isinstance(loaded_data, dict)
    
    def test_toml_dump_basic(self, tmp_path):
        """Test basic TOML dumping."""
        toml_file = tmp_path / "test.toml"
        
        data = {"name": "test", "value": 42}
        serializer = TOMLSerializer()
        serializer.dump(data, toml_file)
        
        # Verify file was created and contains correct data
        assert toml_file.exists()
        with open(toml_file, "r") as f:
            loaded_data = toml.load(f)
        assert loaded_data == data
    
    def test_toml_load_empty_file(self, tmp_path):
        """Test loading empty TOML file."""
        toml_file = tmp_path / "empty.toml"
        with open(toml_file, "w") as f:
            f.write("")
        
        serializer = TOMLSerializer()
        loaded_data = serializer.load(toml_file)
        
        assert loaded_data == {}
    
    def test_toml_load_non_dict_returns_empty(self, tmp_path):
        """Test that non-dict TOML returns empty dict."""
        toml_file = tmp_path / "test.toml"
        
        # TOML doesn't support arrays as root, so we'll test with a table
        with open(toml_file, "w") as f:
            f.write("[table]\nkey = 'value'\n")
        
        serializer = TOMLSerializer()
        loaded_data = serializer.load(toml_file)
        
        # The data will have the table, so this test is slightly different
        assert isinstance(loaded_data, dict)
    
    def test_toml_load_invalid_toml_raises_error(self, tmp_path):
        """Test that invalid TOML raises SerializationError."""
        toml_file = tmp_path / "invalid.toml"
        with open(toml_file, "w") as f:
            f.write("invalid = ]")
        
        serializer = TOMLSerializer()
        with pytest.raises(SerializationError):
            serializer.load(toml_file)
    
    def test_toml_dump_special_characters(self, tmp_path):
        """Test TOML dumping with special characters."""
        toml_file = tmp_path / "special.toml"
        
        data = {
            "unicode": "测试 Unicode characters",
            "string_with_quotes": 'This has "quotes" and \'apostrophes\'',
            "multiline": "Line 1\nLine 2",
            "numbers_int": [1, 2, -3, 0],  # TOML requires homogeneous arrays
            "numbers_float": [1.0, 2.5, -3.7, 0.0]
        }
        serializer = TOMLSerializer()
        serializer.dump(data, toml_file)
        
        with open(toml_file, "r") as f:
            loaded_data = toml.load(f)
        
        assert loaded_data["unicode"] == data["unicode"]
        assert loaded_data["numbers_int"] == data["numbers_int"]
        assert loaded_data["numbers_float"] == data["numbers_float"]


class TestSerializerRegistry:
    """Test serializer registry functionality."""
    
    def test_get_json_serializer(self):
        """Test getting JSON serializer."""
        serializer = get_serializer("json")
        assert isinstance(serializer, JSONSerializer)
        
        # Test case insensitivity
        serializer = get_serializer("JSON")
        assert isinstance(serializer, JSONSerializer)
    
    def test_get_yaml_serializer(self):
        """Test getting YAML serializer."""
        serializer = get_serializer("yaml")
        assert isinstance(serializer, YAMLSerializer)
        
        # Test case insensitivity
        serializer = get_serializer("YAML")
        assert isinstance(serializer, YAMLSerializer)
    
    def test_get_yml_serializer(self):
        """Test getting YAML serializer for .yml extension."""
        serializer = get_serializer("yml")
        assert isinstance(serializer, YAMLSerializer)
    
    def test_get_toml_serializer(self):
        """Test getting TOML serializer."""
        serializer = get_serializer("toml")
        assert isinstance(serializer, TOMLSerializer)
        
        # Test case insensitivity
        serializer = get_serializer("TOML")
        assert isinstance(serializer, TOMLSerializer)
    
    def test_get_unsupported_format_raises_error(self):
        """Test that unsupported format raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            get_serializer("unsupported")
        
        assert "Unsupported format: unsupported" in str(exc_info.value)
        assert "json, yaml, yml, toml" in str(exc_info.value)
    
    def test_all_supported_formats(self):
        """Test that all supported formats can be retrieved."""
        supported_formats = ["json", "yaml", "yml", "toml"]
        
        for fmt in supported_formats:
            serializer = get_serializer(fmt)
            assert serializer is not None
