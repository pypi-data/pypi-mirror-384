"""Learning processor interfaces following SOLID principles."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from ..schemas.learning import LearningResponse, LearningContext


class SessionRetriever(ABC):
    """Interface for retrieving session data for learning."""
    
    @abstractmethod
    async def retrieve_sessions(self, 
                              team_identifier: str, 
                              agent_name: str, 
                              session_limit: int,
                              team_wide_learning: bool = False) -> List[Dict[str, Any]]:
        """Retrieve sessions for learning.
        
        Args:
            team_identifier: Team identifier
            agent_name: Agent name for filtering
            session_limit: Maximum number of sessions
            team_wide_learning: Whether to include all team sessions
            
        Returns:
            List of session dictionaries
        """
        pass


class LearningAgentExecutor(ABC):
    """Interface for executing learning agents."""
    
    @abstractmethod
    async def execute_learning_agent(self,
                                   learning_agent_config: Dict[str, Any],
                                   target_agent_name: str,
                                   current_memory: str,
                                   sessions: List[Dict[str, Any]],
                                   learning_context: LearningContext,
                                   progress_callback = None) -> Optional[str]:
        """Execute learning agent to generate new memory.
        
        Args:
            learning_agent_config: Learning agent configuration
            target_agent_name: Name of agent being improved
            current_memory: Current agent memory
            sessions: Session data for learning
            learning_context: Learning context
            progress_callback: Optional progress callback
            
        Returns:
            New memory string or None if no changes
        """
        pass


class MemoryComparer(ABC):
    """Interface for comparing memory states."""
    
    @abstractmethod
    def has_changes(self, 
                   current_memory: str, 
                   new_memory: Optional[str]) -> bool:
        """Compare current and new memory to detect changes.
        
        Args:
            current_memory: Current memory state
            new_memory: New memory state
            
        Returns:
            True if there are meaningful changes
        """
        pass


class MemoryUpdater(ABC):
    """Interface for updating agent memory."""
    
    @abstractmethod
    async def update_memory(self,
                          team_path: str,
                          agent_name: str,
                          new_memory: str) -> Optional[str]:
        """Update agent memory.
        
        Args:
            team_path: Path to team configuration
            agent_name: Name of the agent
            new_memory: New memory to store
            
        Returns:
            Backup path if created, None otherwise
        """
        pass


class ProgressReporter(ABC):
    """Interface for reporting learning progress."""
    
    @abstractmethod
    def report_session_retrieval_start(self, agent_name: str, team_identifier: str) -> None:
        """Report session retrieval start."""
        pass
    
    @abstractmethod
    def report_sessions_retrieved(self, agent_name: str, session_count: int, time_period: str) -> None:
        """Report sessions retrieved."""
        pass
    
    @abstractmethod
    def report_learning_start(self, agent_name: str, session_id: str) -> None:
        """Report learning agent execution start."""
        pass
    
    @abstractmethod
    def report_learning_complete(self, agent_name: str, has_changes: bool) -> None:
        """Report learning agent execution complete."""
        pass
    
    @abstractmethod
    def report_memory_updated(self, agent_name: str, backup_path: str) -> None:
        """Report memory update complete."""
        pass