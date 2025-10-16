"""Memory-focused learning processor following SOLID principles."""

import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

from ..schemas.learning import (
    LearningRequest, 
    LearningResponse, 
    LearningError,
    LearningConfig,
    LearningContext,
    SessionContext as LearningSessionContext
)
from ..utils.logging import get_logger
from .factory import create_memory_manager
from .interfaces import (
    SessionRetriever,
    LearningAgentExecutor, 
    MemoryUpdater,
    ProgressReporter
)
from .services import (
    DatabaseSessionRetriever,
    TeamRunnerLearningAgentExecutor,
    ProviderMemoryUpdater,
    CallbackProgressReporter
)

logger = get_logger(__name__)


class MemoryLearningProcessor:
    """
    Memory-focused learning processor following SOLID principles.
    
    Single Responsibility: Orchestrates the learning process for agent memory
    Open/Closed: Extensible through dependency injection of services
    Liskov Substitution: All services implement their respective interfaces
    Interface Segregation: Each service has a focused interface
    Dependency Inversion: Depends on abstractions, not concrete implementations
    """
    
    def __init__(self,
                 session_retriever: SessionRetriever,
                 learning_executor: LearningAgentExecutor,
                 memory_updater: MemoryUpdater,
                 progress_reporter: Optional[ProgressReporter] = None):
        """Initialize learning processor with injected dependencies.
        
        Args:
            session_retriever: Service for retrieving session data
            learning_executor: Service for executing learning agents
            memory_updater: Service for updating memory
            progress_reporter: Optional service for progress reporting
        """
        self.session_retriever = session_retriever
        self.learning_executor = learning_executor
        self.memory_updater = memory_updater
        self.progress_reporter = progress_reporter
    
    async def process_agent_learning(self,
                                   team_path: str,
                                   agent_name: str,
                                   team_config: Dict[str, Any],
                                   learning_config: LearningConfig,
                                   team_wide_learning: bool = False) -> LearningResponse:
        """Process learning for a single agent.
        
        Args:
            team_path: Path to team configuration
            agent_name: Name of agent to improve
            team_config: Full team configuration
            learning_config: Learning configuration
            team_wide_learning: Whether to use team-wide sessions
            
        Returns:
            Learning response with results
            
        Raises:
            LearningError: If learning processing fails
        """
        try:
            logger.info(f"Starting memory learning for agent: {agent_name}")
            
            # Step 1: Get current agent memory
            current_memory = await self._get_current_memory(team_path, agent_name)
            logger.debug(f"Current memory for {agent_name}: {current_memory}")
            
            # Step 2: Retrieve sessions for learning
            team_identifier = self._extract_team_identifier(team_config)
            
            if self.progress_reporter:
                self.progress_reporter.report_session_retrieval_start(agent_name, team_identifier)
            
            sessions = await self.session_retriever.retrieve_sessions(
                team_identifier=team_identifier,
                agent_name=agent_name,
                session_limit=learning_config.session_limit,
                team_wide_learning=team_wide_learning
            )
            
            if self.progress_reporter and sessions:
                time_period = self._calculate_time_period(sessions)
                self.progress_reporter.report_sessions_retrieved(agent_name, len(sessions), time_period)
            
            # Step 3: Check if we have sessions to learn from
            if not sessions:
                logger.warning(f"No sessions found for agent {agent_name}")
                return LearningResponse(
                    agent_name=agent_name,
                    original_memory=current_memory,
                    updated_memory=None,
                    has_changes=False,
                    learning_summary="No sessions found for learning",
                    confidence_score=0.0
                )
            
            # Step 4: Create learning context
            learning_context = LearningContext(
                team_identifier=team_identifier,
                agent_names=[agent_name],
                session_filters={},
                learning_config=learning_config,
                session_count=len(sessions),
                time_period=self._calculate_time_period(sessions),
                execution_mode=learning_config.execution_mode,
                team_path=team_path
            )
            
            # Step 5: Execute learning agent to generate new memory
            learning_agent_config = self._get_learning_agent_config(team_config, learning_config)
            
            new_memory = await self.learning_executor.execute_learning_agent(
                learning_agent_config=learning_agent_config,
                target_agent_name=agent_name,
                current_memory=current_memory,
                sessions=sessions,
                learning_context=learning_context,
                progress_callback=self.progress_reporter
            )
            
            # Step 6: Update memory if learning agent provided content
            backup_path = None
            has_changes = new_memory is not None and new_memory.strip() != ""
            
            if has_changes:
                backup_path = await self.memory_updater.update_memory(
                    team_path=team_path,
                    agent_name=agent_name,
                    new_memory=new_memory
                )
                
                if self.progress_reporter:
                    self.progress_reporter.report_memory_updated(agent_name, backup_path or "")
                
                learning_summary = f"Updated memory based on {len(sessions)} sessions"
            else:
                learning_summary = f"No memory content provided after analyzing {len(sessions)} sessions"
            
            # Step 8: Create response
            response = LearningResponse(
                agent_name=agent_name,
                original_memory=current_memory,
                updated_memory=new_memory if has_changes else None,
                has_changes=has_changes,
                learning_summary=learning_summary,
                confidence_score=0.8 if has_changes else 0.2
            )
            
            logger.info(f"Completed memory learning for {agent_name}: {learning_summary}")
            return response
            
        except Exception as e:
            logger.error(f"Memory learning failed for {agent_name}: {e}")
            raise LearningError(f"Agent learning failed: {e}", "MEMORY_LEARNING_ERROR", agent_name)
    
    async def _get_current_memory(self, team_path: str, agent_name: str) -> str:
        """Get current agent memory."""
        try:
            # For simplicity, create a temporary memory manager to get current memory
            # In production, this could be injected as another dependency
            memory_manager = create_memory_manager()
            memory = await memory_manager.get_agent_memory(team_path, agent_name)
            return memory or ""
            
        except Exception as e:
            logger.error(f"Failed to get current memory for {agent_name}: {e}")
            return ""
    
    def _extract_team_identifier(self, team_config: Dict[str, Any]) -> str:
        """Extract team identifier from configuration."""
        return team_config.get("id", team_config.get("name", "unknown"))
    
    def _get_learning_agent_config(self, 
                                 team_config: Dict[str, Any], 
                                 learning_config: LearningConfig) -> Dict[str, Any]:
        """Get learning agent configuration."""
        for agent in team_config.get("agents", []):
            agent_id = agent.get("id") or agent.get("name", "").lower().replace(" ", "_")
            if agent_id == learning_config.learning_agent:
                return agent
        
        raise LearningError(
            f"Learning agent {learning_config.learning_agent} not found", 
            "LEARNING_AGENT_NOT_FOUND"
        )
    
    def _calculate_time_period(self, sessions: List[Dict[str, Any]]) -> str:
        """Calculate time period covered by sessions."""
        if not sessions:
            return "No sessions"
        
        try:
            timestamps = []
            for session in sessions:
                if "created_at" in session:
                    timestamps.append(datetime.fromisoformat(session["created_at"].replace('Z', '+00:00')))
            
            if not timestamps:
                return "Unknown period"
            
            start_time = min(timestamps)
            end_time = max(timestamps)
            duration = end_time - start_time
            
            return f"{start_time.strftime('%Y-%m-%d')} to {end_time.strftime('%Y-%m-%d')} ({duration.days} days)"
            
        except Exception:
            return "Unknown period"


class MemoryLearningProcessorFactory:
    """Factory for creating memory learning processor with proper dependencies."""
    
    @staticmethod
    def create_processor(database_url: Optional[str] = None, 
                        progress_callback = None) -> MemoryLearningProcessor:
        """Create memory learning processor with all dependencies.
        
        Args:
            database_url: Database URL for session retrieval
            progress_callback: Optional progress callback
            
        Returns:
            Configured MemoryLearningProcessor instance
        """
        # Create services following dependency injection pattern
        session_retriever = DatabaseSessionRetriever(
            database_url or os.getenv('SESSION_DATABASE_URL') or "sqlite+aiosqlite:///conversations.db"
        )
        
        learning_executor = TeamRunnerLearningAgentExecutor()
        
        # Create memory manager based on environment configuration
        memory_manager = create_memory_manager()
        memory_updater = ProviderMemoryUpdater(memory_manager)
        
        # Create progress reporter if callback provided
        progress_reporter = None
        if progress_callback:
            progress_reporter = CallbackProgressReporter(progress_callback)
        
        return MemoryLearningProcessor(
            session_retriever=session_retriever,
            learning_executor=learning_executor,
            memory_updater=memory_updater,
            progress_reporter=progress_reporter
        )