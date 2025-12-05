"""Configuration management for the Content-Based File Organizer."""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml


class ConfigurationError(Exception):
    """Raised when configuration is invalid."""
    pass


class Config:
    """Manages application configuration from YAML files and environment variables.
    
    Environment variables take precedence over YAML configuration.
    Supports default values for all settings.
    """
    
    # Default configuration values
    DEFAULTS = {
        "monitoring": {
            "downloads_path": "~/Downloads",
            "organized_path": "~/Downloads/Organized",
            "file_types": ["pdf", "txt"],
        },
        "llm": {
            "mode": "simulated",
            "bedrock": {
                "model": "anthropic.claude-v2",
                "region": "us-east-1",
                "max_tokens": 50,
            },
        },
        "processing": {
            "content_sample_length": 1000,
            "retry_attempts": 3,
            "retry_delay": 2,
        },
        "logging": {
            "level": "INFO",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
    }
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration.
        
        Args:
            config_path: Path to YAML configuration file. If None, uses defaults.
        """
        self._config: Dict[str, Any] = {}
        self._load_defaults()
        
        if config_path:
            self._load_yaml(config_path)
        
        self._load_env_overrides()
        self._validate()
    
    def _load_defaults(self) -> None:
        """Load default configuration values."""
        self._config = self._deep_copy(self.DEFAULTS)
    
    def _deep_copy(self, obj: Any) -> Any:
        """Deep copy a nested dictionary."""
        if isinstance(obj, dict):
            return {k: self._deep_copy(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._deep_copy(item) for item in obj]
        else:
            return obj
    
    def _load_yaml(self, config_path: str) -> None:
        """Load configuration from YAML file.
        
        Args:
            config_path: Path to YAML configuration file.
            
        Raises:
            ConfigurationError: If file cannot be read or parsed.
        """
        try:
            path = Path(config_path).expanduser()
            if not path.exists():
                raise ConfigurationError(f"Configuration file not found: {config_path}")
            
            with open(path, 'r') as f:
                yaml_config = yaml.safe_load(f)
            
            if yaml_config is None:
                return
            
            if not isinstance(yaml_config, dict):
                raise ConfigurationError("Configuration file must contain a YAML dictionary")
            
            self._merge_config(self._config, yaml_config)
            
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Failed to parse YAML configuration: {e}")
        except IOError as e:
            raise ConfigurationError(f"Failed to read configuration file: {e}")
    
    def _merge_config(self, base: Dict[str, Any], override: Dict[str, Any]) -> None:
        """Merge override configuration into base configuration.
        
        Args:
            base: Base configuration dictionary (modified in place).
            override: Override configuration dictionary.
        """
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value
    
    def _load_env_overrides(self) -> None:
        """Load configuration overrides from environment variables.
        
        Environment variables follow the pattern: SECTION_KEY
        Examples:
            - DOWNLOADS_PATH overrides monitoring.downloads_path
            - LLM_MODE overrides llm.mode
            - BEDROCK_MODEL overrides llm.bedrock.model
        """
        # Monitoring section
        if env_val := os.getenv("DOWNLOADS_PATH"):
            self._config["monitoring"]["downloads_path"] = env_val
        
        if env_val := os.getenv("ORGANIZED_PATH"):
            self._config["monitoring"]["organized_path"] = env_val
        
        # LLM section
        if env_val := os.getenv("LLM_MODE"):
            self._config["llm"]["mode"] = env_val
        
        if env_val := os.getenv("BEDROCK_MODEL"):
            self._config["llm"]["bedrock"]["model"] = env_val
        
        if env_val := os.getenv("BEDROCK_REGION"):
            self._config["llm"]["bedrock"]["region"] = env_val
        
        if env_val := os.getenv("BEDROCK_MAX_TOKENS"):
            try:
                self._config["llm"]["bedrock"]["max_tokens"] = int(env_val)
            except ValueError:
                raise ConfigurationError(f"BEDROCK_MAX_TOKENS must be an integer: {env_val}")
        
        # Processing section
        if env_val := os.getenv("CONTENT_SAMPLE_LENGTH"):
            try:
                self._config["processing"]["content_sample_length"] = int(env_val)
            except ValueError:
                raise ConfigurationError(f"CONTENT_SAMPLE_LENGTH must be an integer: {env_val}")
        
        if env_val := os.getenv("RETRY_ATTEMPTS"):
            try:
                self._config["processing"]["retry_attempts"] = int(env_val)
            except ValueError:
                raise ConfigurationError(f"RETRY_ATTEMPTS must be an integer: {env_val}")
        
        if env_val := os.getenv("RETRY_DELAY"):
            try:
                self._config["processing"]["retry_delay"] = int(env_val)
            except ValueError:
                raise ConfigurationError(f"RETRY_DELAY must be an integer: {env_val}")
        
        # Logging section
        if env_val := os.getenv("LOG_LEVEL"):
            self._config["logging"]["level"] = env_val
    
    def _validate(self) -> None:
        """Validate configuration values.
        
        Raises:
            ConfigurationError: If configuration is invalid.
        """
        # Validate LLM mode
        valid_modes = ["simulated", "bedrock"]
        llm_mode = self._config["llm"]["mode"]
        if llm_mode not in valid_modes:
            raise ConfigurationError(
                f"Invalid LLM mode: {llm_mode}. Must be one of {valid_modes}"
            )
        
        # Validate file types
        file_types = self._config["monitoring"]["file_types"]
        if not isinstance(file_types, list) or not file_types:
            raise ConfigurationError("file_types must be a non-empty list")
        
        for file_type in file_types:
            if not isinstance(file_type, str):
                raise ConfigurationError(f"Invalid file type: {file_type}. Must be a string")
        
        # Validate positive integers
        if self._config["processing"]["content_sample_length"] <= 0:
            raise ConfigurationError("content_sample_length must be positive")
        
        if self._config["processing"]["retry_attempts"] < 0:
            raise ConfigurationError("retry_attempts must be non-negative")
        
        if self._config["processing"]["retry_delay"] < 0:
            raise ConfigurationError("retry_delay must be non-negative")
        
        if self._config["llm"]["bedrock"]["max_tokens"] <= 0:
            raise ConfigurationError("max_tokens must be positive")
        
        # Validate log level
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        log_level = self._config["logging"]["level"]
        if log_level not in valid_log_levels:
            raise ConfigurationError(
                f"Invalid log level: {log_level}. Must be one of {valid_log_levels}"
            )
    
    # Property accessors for easy access to configuration values
    
    @property
    def downloads_path(self) -> str:
        """Get the downloads folder path."""
        return str(Path(self._config["monitoring"]["downloads_path"]).expanduser())
    
    @property
    def organized_path(self) -> str:
        """Get the organized folder path."""
        return str(Path(self._config["monitoring"]["organized_path"]).expanduser())
    
    @property
    def file_types(self) -> List[str]:
        """Get the list of monitored file types."""
        return self._config["monitoring"]["file_types"]
    
    @property
    def llm_mode(self) -> str:
        """Get the LLM mode (simulated or bedrock)."""
        return self._config["llm"]["mode"]
    
    @property
    def bedrock_model(self) -> str:
        """Get the Bedrock model identifier."""
        return self._config["llm"]["bedrock"]["model"]
    
    @property
    def bedrock_region(self) -> str:
        """Get the Bedrock AWS region."""
        return self._config["llm"]["bedrock"]["region"]
    
    @property
    def bedrock_max_tokens(self) -> int:
        """Get the Bedrock max tokens."""
        return self._config["llm"]["bedrock"]["max_tokens"]
    
    @property
    def content_sample_length(self) -> int:
        """Get the content sample length."""
        return self._config["processing"]["content_sample_length"]
    
    @property
    def retry_attempts(self) -> int:
        """Get the number of retry attempts."""
        return self._config["processing"]["retry_attempts"]
    
    @property
    def retry_delay(self) -> int:
        """Get the retry delay in seconds."""
        return self._config["processing"]["retry_delay"]
    
    @property
    def log_level(self) -> str:
        """Get the logging level."""
        return self._config["logging"]["level"]
    
    @property
    def log_format(self) -> str:
        """Get the logging format string."""
        return self._config["logging"]["format"]
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by dot-notation key.
        
        Args:
            key: Configuration key in dot notation (e.g., "llm.mode")
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key.split(".")
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
