"""
Base runner with common functionality
"""

import logging
from typing import Optional, Dict, Any
from agents import RunConfig
from ...core.team import Team
from ...schemas import SessionContext
from .session_manager import SessionManager
from .cleanup_manager import CleanupManager

logger = logging.getLogger(__name__)


class BaseRunner:
    """Base class for all runners with common functionality."""
    
    def __init__(self, team: Team):
        self.team = team
        self.logger = logging.getLogger(__name__)
        self.session_manager = SessionManager()
        self.cleanup_manager = CleanupManager()
    
    def set_custom_session_provider(self, provider_factory):
        """Set a custom session provider factory function.
        
        Args:
            provider_factory: Function that takes session_id and returns a session provider
        """
        self.session_manager.set_custom_session_provider(provider_factory)
    
    def _create_run_config(self, workflow_name: Optional[str] = None) -> RunConfig:
        """Create a run configuration.
        
        Args:
            workflow_name: Name for the workflow
            
        Returns:
            RunConfig instance
        """
        return RunConfig(
            workflow_name=workflow_name or self.team.name or "Unknown Team"
        )
    
    def _get_session(self, session_id: Optional[str] = None, session_context: Optional[Dict[str, Any]] = None, context_obj: Optional['SessionContext'] = None):
        """Get session for persistence.
        
        Args:
            session_id: Session identifier
            session_context: Session context data (deprecated, use context_obj)
            context_obj: SessionContext object for direct passing
            
        Returns:
            Session instance or None
        """
        # Prefer SessionContext object over dictionary
        if context_obj is not None:
            return self.session_manager.get_session(session_id, context_obj)
        return self.session_manager.get_session(session_id, session_context)
    
    def _log_session_info(self, session, session_id: Optional[str], context: str = ""):
        """Log session information.
        
        Args:
            session: Session instance
            session_id: Session identifier
            context: Additional context for logging
        """
        if session:
            self.logger.info(f"Running {context} with persistent session: {session_id}. Session info: {session}")
        else:
            self.logger.info(f"Running {context} without session persistence")
    
    def _get_effective_max_turns(self, max_turns: Optional[int]) -> Optional[int]:
        """Get effective max turns value.
        
        Args:
            max_turns: Requested max turns
            
        Returns:
            Effective max turns value (None if no limit should be applied)
        """
        # Return the provided max_turns if it's not None
        if max_turns is not None:
            return max_turns
        
        # Return team's max_turns if it's not None
        if self.team.max_turns is not None:
            return self.team.max_turns
        
        # Return None if no max_turns is configured (no limit)
        return None
    
    def _enrich_session_context(self, session_context: Optional[Dict[str, Any]], agent_name: str, session_id: Optional[str] = None) -> SessionContext:
        """Enrich session context with team_id and agent_id from YAML configuration.
        
        Args:
            session_context: Original session context (may be None)
            agent_name: Current agent name
            session_id: Session ID for this execution
            
        Returns:
            SessionContext object with team_id and agent_id populated
        """
        # Start with existing session context or empty dict
        existing_context = session_context.copy() if session_context else {}
        
        # Extract team_id, team_identifier and account_id from existing context or YAML root fields
        team_identifier = existing_context.get('team_identifier')  # Team directory identifier
        team_id = None  # Integer ID for Gnosari Cloud linking
        account_id = existing_context.get('account_id')  # Preserve existing if present
        
        # Extract team_id from YAML config (for Gnosari Cloud linking)
        if self.team.original_config and isinstance(self.team.original_config, dict):
            team_id = self.team.original_config.get('id')
            
        # Extract account_id from YAML root 'account_id' field if not already set
        if account_id is None and self.team.original_config and isinstance(self.team.original_config, dict):
            yaml_account_id = self.team.original_config.get('account_id')
            if yaml_account_id is not None:
                account_id = int(yaml_account_id)  # Ensure it's an integer
        
        # Get agent identifier from agent name using team mapping
        agent_identifier = self.team.name_to_agent_id.get(agent_name, agent_name)  # Fallback to name if not found
        
        # Extract integer IDs from existing context (for python-api compatibility)
        team_id_int = existing_context.get('team_id') if isinstance(existing_context.get('team_id'), int) else None
        agent_id_int = existing_context.get('agent_id') if isinstance(existing_context.get('agent_id'), int) else None
        
        # Build context data with required fields
        context_data = {
            # Integer IDs for python-api database compatibility
            'team_id': team_id_int,
            'agent_id': agent_id_int,
            # String identifiers from YAML - prefer YAML team ID over folder name
            'team_identifier': team_id or team_identifier or 'unknown',
            'agent_identifier': agent_identifier,
            'account_id': account_id,
            'session_id': session_id or existing_context.get('session_id'),
            'original_config': self.team.original_config or {},
            'metadata': existing_context.get('metadata', {})
        }
        
        # Create and validate SessionContext
        try:
            return SessionContext(**context_data)
        except Exception as e:
            self.logger.warning(f"Failed to create SessionContext: {e}, using defaults")
            # Return with minimal required fields and defaults
            return SessionContext(
                team_id='unknown',
                agent_id=agent_id,
                original_config={},
                metadata={}
            )