"""Memory manager for coordinating memory operations."""

from typing import Dict, Any, Optional
from ..schemas.learning import LearningError
from ..utils.logging import get_logger
from .providers.base import MemoryProvider

logger = get_logger(__name__)


class MemoryManager:
    """Memory manager that coordinates memory operations through providers.
    
    Follows Single Responsibility Principle by delegating storage specifics
    to provider implementations while coordinating operations.
    """
    
    def __init__(self, provider: MemoryProvider):
        """Initialize memory manager with a specific provider.
        
        Args:
            provider: Memory provider implementation (YAML, database, etc.)
        """
        self._provider = provider
    
    @property
    def provider(self) -> MemoryProvider:
        """Get the current memory provider."""
        return self._provider
    
    async def get_agent_memory(self, team_path: str, agent_name: str) -> str:
        """Retrieve agent memory, returning empty string if not found.
        
        Args:
            team_path: Path to team configuration
            agent_name: Name of the agent
            
        Returns:
            Agent memory string (empty if not found)
            
        Raises:
            LearningError: If memory retrieval fails
        """
        try:
            memory = await self._provider.get_agent_memory(team_path, agent_name)
            return memory if memory is not None else ""
            
        except Exception as e:
            logger.error(f"Failed to get memory for agent {agent_name}: {e}")
            raise LearningError(f"Memory retrieval failed: {e}", "MEMORY_RETRIEVAL_ERROR")
    
    async def update_agent_memory(self, 
                                team_path: str, 
                                agent_name: str, 
                                new_memory: str) -> Optional[str]:
        """Update agent memory.
        
        Args:
            team_path: Path to team configuration
            agent_name: Name of the agent
            new_memory: New memory string to store
            
        Returns:
            Backup path if backup was created, None otherwise
            
        Raises:
            LearningError: If memory update fails
        """
        try:
            if not new_memory:
                logger.info(f"No memory changes to update for agent {agent_name}")
                return None
            
            backup_path = await self._provider.update_agent_memory(
                team_path, agent_name, new_memory
            )
            
            logger.info(f"Successfully updated memory for agent {agent_name}")
            return backup_path
            
        except Exception as e:
            logger.error(f"Failed to update memory for agent {agent_name}: {e}")
            raise LearningError(f"Memory update failed: {e}", "MEMORY_UPDATE_ERROR")
    
    async def validate_configuration(self, team_path: str) -> bool:
        """Validate team configuration for memory operations.
        
        Args:
            team_path: Path to team configuration
            
        Returns:
            True if configuration is valid
            
        Raises:
            LearningError: If configuration is invalid
        """
        try:
            return await self._provider.validate_configuration(team_path)
            
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            raise LearningError(f"Configuration validation failed: {e}", "VALIDATION_ERROR")
    
    async def merge_memory(self, 
                         existing_memory: Dict[str, Any], 
                         new_memory: Dict[str, Any]) -> Dict[str, Any]:
        """Merge existing and new memory dictionaries.
        
        Args:
            existing_memory: Current agent memory
            new_memory: New memory to merge
            
        Returns:
            Merged memory dictionary
        """
        if not new_memory:
            return existing_memory
        
        if not existing_memory:
            return new_memory
        
        # Deep merge dictionaries (new takes precedence)
        merged = existing_memory.copy()
        merged.update(new_memory)
        
        return merged
    
    async def close(self):
        """Close memory provider resources."""
        if hasattr(self._provider, 'close'):
            await self._provider.close()