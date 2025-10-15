from typing import Optional, Dict, Any
from ..learning_processor import MemoryLearningProcessor
from ..session_services.learning_session_service import LearningSessionService
from ..interfaces import SessionRetriever, LearningAgentExecutor, MemoryUpdater, ProgressReporter
from ...schemas.learning import LearningResponse, LearningConfig, LearningContext
from ...schemas.session import SessionContext
from ...utils.logging import get_logger

logger = get_logger(__name__)


class EnhancedMemoryLearningProcessor(MemoryLearningProcessor):
    """Enhanced learning processor with session storage capability."""
    
    def __init__(self,
                 session_retriever: SessionRetriever,
                 learning_executor: LearningAgentExecutor,
                 memory_updater: MemoryUpdater,
                 progress_reporter: Optional[ProgressReporter] = None,
                 learning_session_service: Optional[LearningSessionService] = None):
        """Initialize enhanced processor with session storage capability.
        
        Args:
            session_retriever: Service for retrieving session data
            learning_executor: Service for executing learning agents
            memory_updater: Service for updating memory
            progress_reporter: Optional service for progress reporting
            learning_session_service: Optional service for learning session storage
        """
        super().__init__(session_retriever, learning_executor, memory_updater, progress_reporter)
        self.learning_session_service = learning_session_service
    
    async def process_agent_learning(self, 
                                   team_path: str,
                                   agent_name: str,
                                   team_config: Dict[str, Any],
                                   learning_config: LearningConfig,
                                   team_wide_learning: bool = False,
                                   session_context: Optional[SessionContext] = None) -> LearningResponse:
        """Process agent learning with optional session storage.
        
        Args:
            team_path: Path to team configuration
            agent_name: Name of agent to improve
            team_config: Full team configuration
            learning_config: Learning configuration
            team_wide_learning: Whether to use team-wide sessions
            session_context: Optional session context for storage
            
        Returns:
            Learning response with results
        """
        # Call parent implementation to get learning response
        learning_response = await super().process_agent_learning(
            team_path, agent_name, team_config, learning_config, team_wide_learning
        )
        
        # Store learning session if service is configured and session context provided
        if self.learning_session_service and session_context:
            try:
                # Create learning context for storage
                learning_context = self._create_learning_context(team_config, learning_config, team_path)
                
                await self.learning_session_service.store_learning_session(
                    learning_response, learning_context, team_config, session_context
                )
                logger.info(f"Stored learning session for agent {agent_name}")
                
            except Exception as e:
                logger.warning(f"Failed to store learning session for {agent_name}: {e}")
                # Don't fail the learning process if storage fails
        
        return learning_response
    
    def _create_learning_context(self, 
                               team_config: Dict[str, Any], 
                               learning_config: LearningConfig, 
                               team_path: str) -> LearningContext:
        """Create learning context for session storage.
        
        Args:
            team_config: Team configuration dictionary
            learning_config: Learning configuration
            team_path: Path to team configuration
            
        Returns:
            LearningContext for session storage
        """
        team_identifier = self._extract_team_identifier(team_config)
        
        return LearningContext(
            team_identifier=team_identifier,
            agent_names=[],  # Will be populated by service
            session_filters={},
            learning_config=learning_config,
            session_count=None,
            time_period=None,
            execution_mode=learning_config.execution_mode,
            team_path=team_path
        )