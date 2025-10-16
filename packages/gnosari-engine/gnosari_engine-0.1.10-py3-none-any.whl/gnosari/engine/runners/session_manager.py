"""
Session lifecycle management for runners
"""

import logging
from typing import Optional, Dict, Any
from agents.memory.session import SessionABC

logger = logging.getLogger(__name__)


class SessionManager:
    """Manages session lifecycle for runners."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._custom_session_provider = None
    
    def set_custom_session_provider(self, provider_factory):
        """Set a custom session provider factory function.
        
        Args:
            provider_factory: Function that takes session_id and returns a session provider
        """
        self._custom_session_provider = provider_factory
    
    def get_session(self, session_id: Optional[str] = None, session_context: Optional[Dict[str, Any]] = None) -> Optional[SessionABC]:
        """Get session for persistence based on environment configuration.
        
        Args:
            session_id: Session identifier
            session_context: Session context data
            
        Returns:
            Session instance or None if no session_id provided
        """
        if not session_id:
            self.logger.info("No session_id provided - running without persistent memory")
            return None
        
        # Use custom session provider if set
        if self._custom_session_provider:
            try:
                session = self._custom_session_provider(session_id)
                if session:
                    self.logger.info(f"Using custom session provider for session: {session_id}")
                    return session
            except Exception as e:
                self.logger.error(f"Custom session provider failed: {e}, falling back to default")
        
        # Always use GnosariContextSession for all providers
        try:
            from ...sessions import GnosariContextSession
            self.logger.info(f"Using Gnosari context session for session: {session_id}, context: {session_context}")
            return GnosariContextSession(session_id, session_context)
        except ImportError as e:
            self.logger.error(f"Failed to import GnosariContextSession: {e}")
            raise
    
    async def cleanup_session(self, session: Optional[SessionABC]) -> None:
        """Clean up session resources.
        
        Args:
            session: Session to cleanup
        """
        if session and hasattr(session, 'cleanup'):
            try:
                await session.cleanup()
                self.logger.debug(f"Cleaned up session")
            except Exception as e:
                self.logger.error(f"Error cleaning up session: {e}")