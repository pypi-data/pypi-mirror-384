"""Environment variable substitution functionality."""

import os
import re
import logging
from typing import Any


class EnvironmentVariableSubstitutor:
    """Handles environment variable substitution in configuration objects."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def substitute(self, obj: Any) -> Any:
        """
        Recursively substitute environment variables in a configuration object.
        
        Supports ${VAR_NAME} and ${VAR_NAME:default_value} syntax.
        
        Args:
            obj: Configuration object (dict, list, string, etc.)
            
        Returns:
            Object with environment variables substituted
        """
        if isinstance(obj, dict):
            return {key: self.substitute(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self.substitute(item) for item in obj]
        elif isinstance(obj, str):
            return self._substitute_in_string(obj)
        else:
            return obj
    
    def _substitute_in_string(self, content: str) -> str:
        """Substitute environment variables in a string."""
        pattern = r'\$\{([^}:]+)(?::([^}]*))?\}'
        
        def replace_var(match):
            var_name = match.group(1)
            default_value = match.group(2) if match.group(2) is not None else ""
            
            env_value = os.getenv(var_name)
            
            self.logger.debug(f"Processing env var: {var_name}, value: {env_value}, default: {default_value}")
            
            if env_value is not None:
                self.logger.debug(f"Substituting ${{{var_name}}} with env value: {env_value}")
                return self._convert_type(env_value)
            else:
                self.logger.debug(f"Substituting ${{{var_name}}} with default value: {default_value}")
                return self._convert_type(default_value)
        
        return re.sub(pattern, replace_var, content)
    
    def _convert_type(self, value: str) -> str:
        """Convert string value to appropriate Python type."""
        if not isinstance(value, str):
            return str(value)
            
        # Keep all values as strings to avoid sequence type errors
        # The consuming code will handle type conversion as needed
        return value.strip()