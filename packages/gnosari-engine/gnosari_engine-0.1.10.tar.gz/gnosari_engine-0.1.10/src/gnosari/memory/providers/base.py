"""Base memory provider interface."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pathlib import Path


class MemoryProvider(ABC):
    """Abstract base class for memory providers following Single Responsibility Principle."""

    @abstractmethod
    async def get_agent_memory(self, team_path: str, agent_name: str) -> Optional[str]:
        """Retrieve agent memory.
        
        Args:
            team_path: Path to team configuration
            agent_name: Name of the agent
            
        Returns:
            Agent memory string or None if not found
            
        Raises:
            MemoryError: If memory retrieval fails
        """
        pass

    @abstractmethod
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
            MemoryError: If memory update fails
        """
        pass

    @abstractmethod
    async def validate_configuration(self, team_path: str) -> bool:
        """Validate team configuration structure.
        
        Args:
            team_path: Path to team configuration
            
        Returns:
            True if configuration is valid
            
        Raises:
            MemoryError: If configuration is invalid
        """
        pass