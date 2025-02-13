"""Configuration management for the Digital Forensics Triage Tool."""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass
from utils.logging_config import get_logger

logger = get_logger(__name__)

@dataclass
class ScanningConfig:
    max_file_size: int
    min_file_size: int
    parallel_workers: int
    hash_algorithm: str
    excluded_dirs: list[str]
    excluded_extensions: list[str]

@dataclass
class LoggingConfig:
    level: str
    format: str
    file_rotation: int

@dataclass
class OutputConfig:
    base_dir: str
    report_format: str
    compress_results: bool

@dataclass
class SecurityConfig:
    sanitize_paths: bool
    max_symlink_depth: int
    skip_hidden_files: bool
    verify_signatures: bool

@dataclass
class MonitoringConfig:
    scan_timeout: int
    alert_on_timeout: bool
    alert_on_error: bool

class ConfigManager:
    """Manages configuration loading and validation for the forensics tool."""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_path: Optional path to custom config file
        """
        self.config_path = config_path or str(
            Path(__file__).parent / 'default_config.yaml'
        )
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load and validate configuration from file."""
        try:
            # Load default config
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            # Override with environment variables if present
            self._override_from_env(config)
            
            # Validate configuration
            self._validate_config(config)
            
            logger.info(f"Configuration loaded from {self.config_path}")
            return config
            
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            raise
            
    def _override_from_env(self, config: Dict[str, Any]) -> None:
        """Override configuration values from environment variables."""
        env_prefix = "DFT_"
        
        for key in os.environ:
            if key.startswith(env_prefix):
                config_key = key[len(env_prefix):].lower()
                section, _, option = config_key.partition('_')
                
                if section in config and option:
                    try:
                        # Convert value to appropriate type
                        original_value = config[section][option]
                        env_value = os.environ[key]
                        
                        if isinstance(original_value, bool):
                            config[section][option] = env_value.lower() == 'true'
                        elif isinstance(original_value, int):
                            config[section][option] = int(env_value)
                        else:
                            config[section][option] = env_value
                            
                        logger.debug(f"Override {section}.{option} from environment")
                    except (ValueError, KeyError) as e:
                        logger.warning(f"Invalid environment override {key}: {e}")
                        
    def _validate_config(self, config: Dict[str, Any]) -> None:
        """Validate configuration values."""
        required_sections = ['logging', 'scanning', 'output', 'security', 'monitoring']
        
        # Check required sections
        for section in required_sections:
            if section not in config:
                raise ValueError(f"Missing required config section: {section}")
        
        # Validate specific values
        scanning = config['scanning']
        if scanning['max_file_size'] < scanning['min_file_size']:
            raise ValueError("max_file_size must be greater than min_file_size")
            
        if scanning['parallel_workers'] < 1:
            raise ValueError("parallel_workers must be at least 1")
            
    @property
    def scanning(self) -> ScanningConfig:
        """Get scanning configuration."""
        return ScanningConfig(**self.config['scanning'])
        
    @property
    def logging(self) -> LoggingConfig:
        """Get logging configuration."""
        return LoggingConfig(**self.config['logging'])
        
    @property
    def output(self) -> OutputConfig:
        """Get output configuration."""
        return OutputConfig(**self.config['output'])
        
    @property
    def security(self) -> SecurityConfig:
        """Get security configuration."""
        return SecurityConfig(**self.config['security'])
        
    @property
    def monitoring(self) -> MonitoringConfig:
        """Get monitoring configuration."""
        return MonitoringConfig(**self.config['monitoring'])
