from typing import Optional, Dict, Any
from ..repositories.learning_session_repository import LearningSessionRepository
from ..dtos.learning_session_dto import LearningSessionData
from ...schemas.learning import LearningResponse, LearningContext
from ...schemas.session import SessionContext
from ...utils.logging import get_logger

logger = get_logger(__name__)


class LearningSessionService:
    """Service for learning session business logic."""
    
    def __init__(self, repository: LearningSessionRepository):
        """Initialize service with repository dependency.
        
        Args:
            repository: Learning session repository for data operations
        """
        self.repository = repository
    
    def should_store_learning_session(self, team_config: Dict[str, Any], session_context: SessionContext) -> bool:
        """Determine if learning session should be stored based on configuration.
        
        Args:
            team_config: Team configuration dictionary
            session_context: Session context containing account_id
            
        Returns:
            True if session should be stored, False otherwise
        """
        # Check if account_id is present in team config or session context
        has_account_id = (
            (team_config and team_config.get('account_id') is not None) or
            (session_context and session_context.account_id is not None)
        )
        
        logger.debug(f"Learning session storage check - account_id present: {has_account_id}")
        return has_account_id
    
    async def store_learning_session(self, 
                                   learning_response: LearningResponse, 
                                   context: LearningContext,
                                   team_config: Dict[str, Any],
                                   session_context: SessionContext) -> None:
        """Store learning session if conditions are met.
        
        Args:
            learning_response: Learning response with results
            context: Learning context with team and agent information
            team_config: Team configuration dictionary
            session_context: Session context with account_id
        """
        if not self.should_store_learning_session(team_config, session_context):
            logger.debug("Skipping learning session storage - no account_id found")
            return
        
        session_data = self._create_session_data(learning_response, context, team_config, session_context)
        await self.repository.create_learning_session(session_data)
        logger.info(f"Stored learning session for agent {learning_response.agent_name}")
    
    def _create_session_data(self, 
                           learning_response: LearningResponse, 
                           context: LearningContext,
                           team_config: Dict[str, Any],
                           session_context: SessionContext) -> LearningSessionData:
        """Create learning session data from response and context.
        
        Args:
            learning_response: Learning response with results
            context: Learning context with team and agent information
            team_config: Team configuration dictionary
            session_context: Session context with account_id
            
        Returns:
            LearningSessionData object ready for storage
        """
        # Extract account_id from team_config or session_context
        account_id = team_config.get('account_id') or session_context.account_id
        
        # Generate session_id if not provided
        session_id = session_context.session_id or f"learning-{context.team_identifier}-{learning_response.agent_name}"
        
        return LearningSessionData(
            team_id=session_context.team_id,
            agent_id=session_context.agent_id,
            team_identifier=session_context.team_identifier or context.team_identifier,
            agent_identifier=session_context.agent_identifier or learning_response.agent_name,
            session_id=session_id,
            previous_memory=learning_response.original_memory,
            updated_memory=learning_response.updated_memory,
            account_id=account_id,
            has_changes=learning_response.has_changes,
            learning_summary=learning_response.learning_summary,
            confidence_score=learning_response.confidence_score
        )