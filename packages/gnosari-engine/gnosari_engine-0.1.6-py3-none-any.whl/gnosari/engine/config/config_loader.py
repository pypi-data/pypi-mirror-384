"""Configuration loading functionality."""

import yaml
import logging
from pathlib import Path
from typing import Dict, Any

from .env_substitutor import EnvironmentVariableSubstitutor
from .validator import ConfigValidator


class ConfigLoader:
    """Loads and processes team configuration from YAML files."""
    
    def __init__(self, env_substitutor: EnvironmentVariableSubstitutor = None, validator: ConfigValidator = None):
        self.env_substitutor = env_substitutor or EnvironmentVariableSubstitutor()
        self.validator = validator or ConfigValidator()
        self.logger = logging.getLogger(__name__)
    
    def load_team_config(self, config_path: str) -> Dict[str, Any]:
        """
        Load team configuration from YAML file with environment variable substitution.
        
        Supports ${VAR_NAME} and ${VAR_NAME:default_value} syntax for environment variables.
        
        Args:
            config_path: Path to the YAML configuration file
            
        Returns:
            Team configuration dictionary with environment variables substituted
        """
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Team configuration file not found: {config_path}")
        
        # Read the raw YAML content as string first
        with open(config_file, 'r') as f:
            yaml_content = f.read()
        
        # Substitute environment variables in the raw YAML string before parsing
        yaml_content = self.env_substitutor._substitute_in_string(yaml_content)
        
        # Now parse the substituted YAML
        config = yaml.safe_load(yaml_content)
        
        # Validate the configuration
        self.validator.validate_team_config(config)
        
        self.logger.debug(f"Successfully loaded team configuration from {config_path}")
        return config