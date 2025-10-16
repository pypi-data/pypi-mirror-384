"""Factory for creating memory managers based on configuration."""

import os
from typing import Optional
from ..schemas.learning import LearningError
from ..utils.logging import get_logger
from .manager import MemoryManager
from .providers.yaml_provider import YamlMemoryProvider
from .providers.database_provider import DatabaseMemoryProvider

logger = get_logger(__name__)


def create_memory_manager(
    provider_type: Optional[str] = None,
    database_url: Optional[str] = None,
    backup_enabled: bool = True
) -> MemoryManager:
    """Factory function to create memory manager based on configuration.
    
    Follows Factory Pattern to create appropriate memory provider
    based on environment variables or explicit parameters.
    
    Args:
        provider_type: Memory provider type ('yaml' or 'database').
                      If None, reads from LEARNING_PROVIDER env var.
        database_url: Database URL for database provider.
                     If None, reads from LEARNING_DATABASE_URL env var.
        backup_enabled: Whether to enable backups for YAML provider.
        
    Returns:
        Configured MemoryManager instance
        
    Raises:
        LearningError: If configuration is invalid or provider cannot be created
    """
    try:
        # Determine provider type from parameter or environment
        if provider_type is None:
            provider_type = os.getenv('LEARNING_PROVIDER', 'yaml').lower()
        
        provider_type = provider_type.lower()
        
        if provider_type == 'yaml':
            return _create_yaml_memory_manager(backup_enabled)
        elif provider_type == 'database':
            return _create_database_memory_manager(database_url)
        else:
            raise LearningError(
                f"Unsupported memory provider type: {provider_type}. "
                f"Supported types: 'yaml', 'database'",
                "UNSUPPORTED_PROVIDER_TYPE"
            )
            
    except LearningError:
        raise
    except Exception as e:
        logger.error(f"Failed to create memory manager: {e}")
        raise LearningError(f"Memory manager creation failed: {e}", "MEMORY_MANAGER_CREATION_ERROR")


def _create_yaml_memory_manager(backup_enabled: bool) -> MemoryManager:
    """Create memory manager with YAML provider.
    
    Args:
        backup_enabled: Whether to enable backups
        
    Returns:
        MemoryManager with YamlMemoryProvider
    """
    try:
        provider = YamlMemoryProvider(backup_enabled=backup_enabled)
        logger.info("Created YAML memory manager")
        return MemoryManager(provider)
        
    except Exception as e:
        raise LearningError(f"Failed to create YAML memory provider: {e}", "YAML_PROVIDER_ERROR")


def _create_database_memory_manager(database_url: Optional[str]) -> MemoryManager:
    """Create memory manager with database provider.
    
    Args:
        database_url: Database connection URL
        
    Returns:
        MemoryManager with DatabaseMemoryProvider
    """
    try:
        # Get database URL from parameter or environment
        if database_url is None:
            database_url = os.getenv('LEARNING_DATABASE_URL')
        
        if not database_url:
            raise LearningError(
                "Database URL is required for database provider. "
                "Set LEARNING_DATABASE_URL environment variable or pass database_url parameter.",
                "MISSING_DATABASE_URL"
            )
        
        provider = DatabaseMemoryProvider(database_url)
        logger.info("Created database memory manager")
        return MemoryManager(provider)
        
    except LearningError:
        raise
    except Exception as e:
        raise LearningError(f"Failed to create database memory provider: {e}", "DATABASE_PROVIDER_ERROR")


def get_default_memory_manager() -> MemoryManager:
    """Get default memory manager based on environment configuration.
    
    Returns:
        Default MemoryManager instance based on environment variables
    """
    return create_memory_manager()