"""Configuration loaders implementing the Strategy pattern."""

import tempfile
import os
from pathlib import Path
from typing import Any, Dict

import yaml

from .interfaces import ConfigurationLoader


class MonolithicConfigLoader(ConfigurationLoader):
    """Loader for monolithic YAML configuration files."""
    
    async def load_configuration(self, path: Path) -> Dict[str, Any]:
        """Load configuration from monolithic YAML file."""
        with open(path, 'r') as f:
            return yaml.safe_load(f)
    
    def get_team_identifier(self, path: Path) -> str:
        """Extract team identifier from file path."""
        return path.stem


class ModularConfigLoader(ConfigurationLoader):
    """Loader for modular configuration directories."""
    
    async def load_configuration(self, path: Path) -> Dict[str, Any]:
        """Load configuration from modular directory."""
        # Import modular configuration system
        from ....engine.config.configuration_manager import ConfigurationManager
        
        config_manager = ConfigurationManager()
        modular_config = await config_manager.load_team_from_directory(path)
        config = await config_manager.convert_to_legacy_format(modular_config)
        
        return config
    
    def get_team_identifier(self, path: Path) -> str:
        """Extract team identifier from directory path."""
        path_parts = path.parts
        if 'teams' in path_parts:
            teams_index = path_parts.index('teams')
            if teams_index + 1 < len(path_parts):
                return path_parts[teams_index + 1]
        
        return path.name


class ConfigurationLoaderFactory:
    """Factory for creating configuration loaders."""
    
    def __init__(self):
        self._loaders = {
            "monolithic": MonolithicConfigLoader(),
            "modular": ModularConfigLoader(),
        }
    
    def create_loader(self, config_type: str) -> ConfigurationLoader:
        """Create a loader for the specified configuration type."""
        loader = self._loaders.get(config_type)
        if not loader:
            raise ValueError(f"Unsupported configuration type: {config_type}")
        return loader
    
    def get_supported_types(self) -> list[str]:
        """Get list of supported configuration types."""
        return list(self._loaders.keys())