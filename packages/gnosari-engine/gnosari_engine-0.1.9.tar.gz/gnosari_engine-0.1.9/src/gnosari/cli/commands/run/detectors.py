"""Configuration detectors implementing the Strategy pattern."""

from pathlib import Path

from .interfaces import ConfigurationDetector


class MonolithicConfigDetector(ConfigurationDetector):
    """Detector for monolithic YAML configuration files."""
    
    def can_handle(self, path: Path) -> bool:
        """Check if this is a monolithic YAML file."""
        return (
            path.is_file() and 
            path.suffix.lower() in ['.yaml', '.yml']
        )
    
    def get_config_type(self) -> str:
        """Get the configuration type name."""
        return "monolithic"


class ModularConfigDetector(ConfigurationDetector):
    """Detector for modular configuration directories."""
    
    def can_handle(self, path: Path) -> bool:
        """Check if this is a modular configuration directory."""
        if not path.is_dir():
            return False
        
        # Check for main.yaml or other indicators of modular structure
        main_config = path / "main.yaml"
        return main_config.exists()
    
    def get_config_type(self) -> str:
        """Get the configuration type name."""
        return "modular"


class ConfigurationDetectorFactory:
    """Factory for creating configuration detectors."""
    
    def __init__(self):
        self._detectors = [
            MonolithicConfigDetector(),
            ModularConfigDetector(),
        ]
    
    def detect_configuration_type(self, path: Path) -> ConfigurationDetector:
        """Detect the configuration type for the given path."""
        for detector in self._detectors:
            if detector.can_handle(path):
                return detector
        
        raise ValueError(f"Unsupported configuration path: {path}")
    
    def get_supported_types(self) -> list[str]:
        """Get list of supported configuration types."""
        return [detector.get_config_type() for detector in self._detectors]