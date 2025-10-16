"""Traits module for agent personality and behavior customization."""

from .manager import TraitManager, TraitManagerInterface
from .exceptions import (
    TraitConfigurationError,
    TraitValidationError, 
    TraitProcessingError
)

__all__ = [
    "TraitManager",
    "TraitManagerInterface", 
    "TraitConfigurationError",
    "TraitValidationError",
    "TraitProcessingError"
]