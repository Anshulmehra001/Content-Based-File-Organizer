"""Unit tests for configuration management."""

import os
import tempfile
from pathlib import Path
import pytest
import yaml

from src.config import Config, ConfigurationError


class TestConfigDefaults:
    """Test default configuration values."""
    
    def test_loads_defaults_when_no_config_file(self):
        """Test that Config loads default values when no config file is provided."""
        config = Config()
        
        assert config.downloads_path.endswith("Downloads")
        assert config.organized_path.endswith(os.path.join("Downloads", "Organized"))
        assert config.file_types == ["pdf", "txt"]
        assert config.llm_mode == "simulated"
        assert config.bedrock_model == "anthropic.claude-v2"
        assert config.bedrock_region == "us-east-1"
        assert config.bedrock_max_tokens == 50
        assert config.content_sample_length == 1000
        assert config.retry_attempts == 3
        assert config.retry_delay == 2
        assert config.log_level == "INFO"
    
    def test_default_file_types_list(self):
        """Test that default file types is a list."""
        config = Config()
        assert isinstance(config.file_types, list)
        assert len(config.file_types) > 0


class TestYAMLParsing:
    """Test YAML configuration file parsing."""
    
    def test_loads_yaml_config_file(self):
        """Test loading configuration from a YAML file."""
        yaml_content = """
monitoring:
  downloads_path: "/custom/downloads"
  organized_path: "/custom/organized"
  file_types:
    - "pdf"
    - "txt"
    - "docx"

llm:
  mode: "bedrock"
  bedrock:
    model: "custom-model"
    region: "us-west-2"
    max_tokens: 100

processing:
  content_sample_length: 2000
  retry_attempts: 5
  retry_delay: 3

logging:
  level: "DEBUG"
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            config_path = f.name
        
        try:
            config = Config(config_path)
            
            # Use os.path.normpath for platform-independent path comparison
            assert os.path.normpath(config.downloads_path) == os.path.normpath("/custom/downloads")
            assert os.path.normpath(config.organized_path) == os.path.normpath("/custom/organized")
            assert config.file_types == ["pdf", "txt", "docx"]
            assert config.llm_mode == "bedrock"
            assert config.bedrock_model == "custom-model"
            assert config.bedrock_region == "us-west-2"
            assert config.bedrock_max_tokens == 100
            assert config.content_sample_length == 2000
            assert config.retry_attempts == 5
            assert config.retry_delay == 3
            assert config.log_level == "DEBUG"
        finally:
            os.unlink(config_path)
    
    def test_partial_yaml_config_uses_defaults(self):
        """Test that partial YAML config merges with defaults."""
        yaml_content = """
llm:
  mode: "bedrock"

processing:
  retry_attempts: 10
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            config_path = f.name
        
        try:
            config = Config(config_path)
            
            # Overridden values
            assert config.llm_mode == "bedrock"
            assert config.retry_attempts == 10
            
            # Default values still present
            assert config.downloads_path.endswith("Downloads")
            assert config.content_sample_length == 1000
            assert config.log_level == "INFO"
        finally:
            os.unlink(config_path)
    
    def test_raises_error_for_nonexistent_file(self):
        """Test that ConfigurationError is raised for non-existent file."""
        with pytest.raises(ConfigurationError, match="Configuration file not found"):
            Config("/nonexistent/path/config.yaml")
    
    def test_raises_error_for_invalid_yaml(self):
        """Test that ConfigurationError is raised for invalid YAML."""
        yaml_content = """
monitoring:
  downloads_path: "/path"
    invalid indentation
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            config_path = f.name
        
        try:
            with pytest.raises(ConfigurationError, match="Failed to parse YAML"):
                Config(config_path)
        finally:
            os.unlink(config_path)
    
    def test_raises_error_for_non_dict_yaml(self):
        """Test that ConfigurationError is raised when YAML is not a dictionary."""
        yaml_content = "just a string"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            config_path = f.name
        
        try:
            with pytest.raises(ConfigurationError, match="must contain a YAML dictionary"):
                Config(config_path)
        finally:
            os.unlink(config_path)
    
    def test_empty_yaml_file_uses_defaults(self):
        """Test that empty YAML file uses default values."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("")
            config_path = f.name
        
        try:
            config = Config(config_path)
            assert config.llm_mode == "simulated"
            assert config.retry_attempts == 3
        finally:
            os.unlink(config_path)


class TestEnvironmentVariableOverrides:
    """Test environment variable overrides."""
    
    def test_env_var_overrides_downloads_path(self, monkeypatch):
        """Test that DOWNLOADS_PATH environment variable overrides config."""
        monkeypatch.setenv("DOWNLOADS_PATH", "/env/downloads")
        config = Config()
        assert os.path.normpath(config.downloads_path) == os.path.normpath("/env/downloads")
    
    def test_env_var_overrides_organized_path(self, monkeypatch):
        """Test that ORGANIZED_PATH environment variable overrides config."""
        monkeypatch.setenv("ORGANIZED_PATH", "/env/organized")
        config = Config()
        assert os.path.normpath(config.organized_path) == os.path.normpath("/env/organized")
    
    def test_env_var_overrides_llm_mode(self, monkeypatch):
        """Test that LLM_MODE environment variable overrides config."""
        monkeypatch.setenv("LLM_MODE", "bedrock")
        config = Config()
        assert config.llm_mode == "bedrock"
    
    def test_env_var_overrides_bedrock_model(self, monkeypatch):
        """Test that BEDROCK_MODEL environment variable overrides config."""
        monkeypatch.setenv("BEDROCK_MODEL", "env-model")
        config = Config()
        assert config.bedrock_model == "env-model"
    
    def test_env_var_overrides_bedrock_region(self, monkeypatch):
        """Test that BEDROCK_REGION environment variable overrides config."""
        monkeypatch.setenv("BEDROCK_REGION", "eu-west-1")
        config = Config()
        assert config.bedrock_region == "eu-west-1"
    
    def test_env_var_overrides_bedrock_max_tokens(self, monkeypatch):
        """Test that BEDROCK_MAX_TOKENS environment variable overrides config."""
        monkeypatch.setenv("BEDROCK_MAX_TOKENS", "200")
        config = Config()
        assert config.bedrock_max_tokens == 200
    
    def test_env_var_overrides_content_sample_length(self, monkeypatch):
        """Test that CONTENT_SAMPLE_LENGTH environment variable overrides config."""
        monkeypatch.setenv("CONTENT_SAMPLE_LENGTH", "500")
        config = Config()
        assert config.content_sample_length == 500
    
    def test_env_var_overrides_retry_attempts(self, monkeypatch):
        """Test that RETRY_ATTEMPTS environment variable overrides config."""
        monkeypatch.setenv("RETRY_ATTEMPTS", "7")
        config = Config()
        assert config.retry_attempts == 7
    
    def test_env_var_overrides_retry_delay(self, monkeypatch):
        """Test that RETRY_DELAY environment variable overrides config."""
        monkeypatch.setenv("RETRY_DELAY", "5")
        config = Config()
        assert config.retry_delay == 5
    
    def test_env_var_overrides_log_level(self, monkeypatch):
        """Test that LOG_LEVEL environment variable overrides config."""
        monkeypatch.setenv("LOG_LEVEL", "ERROR")
        config = Config()
        assert config.log_level == "ERROR"
    
    def test_env_vars_override_yaml_config(self, monkeypatch):
        """Test that environment variables take precedence over YAML config."""
        yaml_content = """
llm:
  mode: "simulated"

processing:
  retry_attempts: 3
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            config_path = f.name
        
        try:
            monkeypatch.setenv("LLM_MODE", "bedrock")
            monkeypatch.setenv("RETRY_ATTEMPTS", "10")
            
            config = Config(config_path)
            
            # Environment variables should override YAML
            assert config.llm_mode == "bedrock"
            assert config.retry_attempts == 10
        finally:
            os.unlink(config_path)
    
    def test_invalid_integer_env_var_raises_error(self, monkeypatch):
        """Test that invalid integer environment variable raises error."""
        monkeypatch.setenv("RETRY_ATTEMPTS", "not-a-number")
        
        with pytest.raises(ConfigurationError, match="must be an integer"):
            Config()


class TestValidation:
    """Test configuration validation logic."""
    
    def test_invalid_llm_mode_raises_error(self):
        """Test that invalid LLM mode raises ConfigurationError."""
        yaml_content = """
llm:
  mode: "invalid-mode"
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            config_path = f.name
        
        try:
            with pytest.raises(ConfigurationError, match="Invalid LLM mode"):
                Config(config_path)
        finally:
            os.unlink(config_path)
    
    def test_empty_file_types_raises_error(self):
        """Test that empty file_types list raises ConfigurationError."""
        yaml_content = """
monitoring:
  file_types: []
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            config_path = f.name
        
        try:
            with pytest.raises(ConfigurationError, match="must be a non-empty list"):
                Config(config_path)
        finally:
            os.unlink(config_path)
    
    def test_non_list_file_types_raises_error(self):
        """Test that non-list file_types raises ConfigurationError."""
        yaml_content = """
monitoring:
  file_types: "pdf"
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            config_path = f.name
        
        try:
            with pytest.raises(ConfigurationError, match="must be a non-empty list"):
                Config(config_path)
        finally:
            os.unlink(config_path)
    
    def test_negative_content_sample_length_raises_error(self):
        """Test that negative content_sample_length raises ConfigurationError."""
        yaml_content = """
processing:
  content_sample_length: -100
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            config_path = f.name
        
        try:
            with pytest.raises(ConfigurationError, match="must be positive"):
                Config(config_path)
        finally:
            os.unlink(config_path)
    
    def test_negative_retry_attempts_raises_error(self):
        """Test that negative retry_attempts raises ConfigurationError."""
        yaml_content = """
processing:
  retry_attempts: -1
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            config_path = f.name
        
        try:
            with pytest.raises(ConfigurationError, match="must be non-negative"):
                Config(config_path)
        finally:
            os.unlink(config_path)
    
    def test_negative_retry_delay_raises_error(self):
        """Test that negative retry_delay raises ConfigurationError."""
        yaml_content = """
processing:
  retry_delay: -5
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            config_path = f.name
        
        try:
            with pytest.raises(ConfigurationError, match="must be non-negative"):
                Config(config_path)
        finally:
            os.unlink(config_path)
    
    def test_invalid_log_level_raises_error(self):
        """Test that invalid log level raises ConfigurationError."""
        yaml_content = """
logging:
  level: "INVALID"
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            config_path = f.name
        
        try:
            with pytest.raises(ConfigurationError, match="Invalid log level"):
                Config(config_path)
        finally:
            os.unlink(config_path)
    
    def test_zero_max_tokens_raises_error(self):
        """Test that zero max_tokens raises ConfigurationError."""
        yaml_content = """
llm:
  bedrock:
    max_tokens: 0
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            config_path = f.name
        
        try:
            with pytest.raises(ConfigurationError, match="must be positive"):
                Config(config_path)
        finally:
            os.unlink(config_path)


class TestConfigAccessors:
    """Test configuration property accessors."""
    
    def test_get_method_with_dot_notation(self):
        """Test get method with dot notation."""
        config = Config()
        
        assert config.get("llm.mode") == "simulated"
        assert config.get("processing.retry_attempts") == 3
        assert config.get("llm.bedrock.model") == "anthropic.claude-v2"
    
    def test_get_method_with_default(self):
        """Test get method returns default for non-existent key."""
        config = Config()
        
        assert config.get("nonexistent.key", "default") == "default"
        assert config.get("llm.nonexistent", None) is None
    
    def test_path_expansion(self):
        """Test that paths with ~ are expanded."""
        yaml_content = """
monitoring:
  downloads_path: "~/custom/downloads"
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            config_path = f.name
        
        try:
            config = Config(config_path)
            
            # Path should be expanded (not contain ~)
            assert "~" not in config.downloads_path
            assert "custom" in config.downloads_path
            assert "downloads" in config.downloads_path
        finally:
            os.unlink(config_path)
