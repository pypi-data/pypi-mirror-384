"""Learning event handler for processing learning.* events following SOLID principles."""

from typing import Dict, Any

from .base import BaseEventHandler
from ...storage.factory import LearningStorageFactory
from ...utils.logging import get_logger

logger = get_logger(__name__)


class LearningEventHandler(BaseEventHandler):
    """Handler for learning events (learning.*).
    
    This class follows the Single Responsibility Principle by handling
    only learning-related events that follow the learning.* pattern.
    """
    
    @property
    def event_type(self) -> str:
        """Return the event type pattern this handler processes."""
        return "learning.*"
    
    def can_handle(self, event_data: Dict[str, Any]) -> bool:
        """Check if this handler can process the given event.
        
        Args:
            event_data: Event data dictionary
            
        Returns:
            bool: True if this handler can process the event
        """
        event_type = event_data.get("event_type", "")
        return event_type.startswith("learning.")
    
    def handle(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process the learning event.
        
        Args:
            event_data: Event data dictionary
            
        Returns:
            Dict[str, Any]: Processing result
        """
        try:
            event_type = event_data.get("event_type")
            data = event_data.get("data", {})
            session = event_data.get("session", {})
            
            logger.info(f"📚 Processing learning event '{event_type}'")
            
            # Route the event based on its specific type
            if event_type == "learning.add_request":
                result = self._handle_add_learning_request(data, session)
            elif event_type.startswith("learning."):
                result = self._handle_generic_learning_event(event_type, data, session)
            else:
                result = self._handle_unknown_learning_event(event_type, data, session)
            
            return self._create_success_response(
                event_data=event_data,
                result=result,
                message=f"Successfully processed learning event '{event_type}'"
            )
            
        except Exception as e:
            logger.error(f"Failed to handle learning event: {e}")
            return self._create_error_response(
                event_data=event_data,
                error=e,
                message=f"Learning event processing failed: {e}"
            )
    
    def _handle_add_learning_request(self, data: Dict[str, Any], session: Dict[str, Any]) -> Dict[str, Any]:
        """Handle learning.add_request events.
        
        Args:
            data: Event data
            session: Session information
            
        Returns:
            Dict[str, Any]: Processing result
        """
        logger.info("Processing add_learning_request event")
        
        # Extract session details
        session_id = session.get("session_id") if session else None
        team_id = session.get("team_id") if session else None
        agent_id = session.get("agent_id") if session else None
        
        # Log the learning request details
        logger.info(f"Learning request from session {session_id}, team {team_id}, agent {agent_id}")
        
        # Store learning using the appropriate storage backend
        try:
            storage = LearningStorageFactory.create_storage()
            learning_stored = storage.store_learning(session, data)
            if learning_stored:
                logger.info("Learning data processed and stored successfully")
            else:
                logger.warning("Failed to store learning data")
        except Exception as e:
            logger.error(f"Error storing learning data: {e}")
            learning_stored = False
        
        return {
            "learning_stored": learning_stored,
            "session_id": session_id,
            "team_id": team_id,
            "agent_id": agent_id,
            "learning_type": "agent_interaction",
            "storage_status": "stored_successfully" if learning_stored else "storage_failed"
        }
    
    def _handle_generic_learning_event(self, event_type: str, data: Dict[str, Any], session: Dict[str, Any]) -> Dict[str, Any]:
        """Handle generic learning.* events.
        
        Args:
            event_type: The specific learning event type
            data: Event data
            session: Session information
            
        Returns:
            Dict[str, Any]: Processing result
        """
        logger.info(f"Processing generic learning event: {event_type}")
        
        return {
            "event_category": "learning",
            "processed_event": event_type,
            "session_id": session.get("session_id") if session else None,
            "processing_status": "acknowledged"
        }
    
    def _handle_unknown_learning_event(self, event_type: str, data: Dict[str, Any], session: Dict[str, Any]) -> Dict[str, Any]:
        """Handle unknown learning events.
        
        Args:
            event_type: The event type
            data: Event data
            session: Session information
            
        Returns:
            Dict[str, Any]: Processing result
        """
        logger.warning(f"Processing unknown learning event: {event_type}")
        
        return {
            "event_category": "unknown_learning",
            "processed_event": event_type,
            "session_id": session.get("session_id") if session else None,
            "processing_status": "unknown_type_handled"
        }
    
