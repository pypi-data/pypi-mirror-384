"""Factory for creating learning storage instances based on configuration."""

import os
from typing import Union

from .base import BaseLearningStorage
from .local_yaml import LocalYAMLLearningStorage
from .gnosari_api import GnosariAPILearningStorage
from ..utils.logging import get_logger

logger = get_logger(__name__)


class LearningStorageFactory:
    """Factory class for creating learning storage instances."""
    
    @staticmethod
    def create_storage() -> BaseLearningStorage:
        """Create a learning storage instance based on environment configuration.
        
        Returns:
            BaseLearningStorage: The appropriate storage implementation
        """
        storage_type = os.getenv("LEARNING_STORAGE", "local").lower()
        
        if storage_type == "gnosari":
            logger.info("Using Gnosari API learning storage")
            return GnosariAPILearningStorage()
        elif storage_type == "local":
            logger.info("Using local YAML learning storage")
            return LocalYAMLLearningStorage()
        else:
            logger.warning(f"Unknown LEARNING_STORAGE type '{storage_type}', defaulting to local YAML storage")
            return LocalYAMLLearningStorage()