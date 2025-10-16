"""Generic event handler for system events following SOLID principles."""

from typing import Dict, Any

from .base import BaseEventHandler
from ...utils.logging import get_logger

logger = get_logger(__name__)


class GenericEventHandler(BaseEventHandler):
    """Handler for generic system events (task.*, user.*, system.*).
    
    This class follows the Single Responsibility Principle by handling
    only generic system events that follow a pattern.
    """
    
    @property
    def event_type(self) -> str:
        """Return the event type pattern this handler processes."""
        return "task.*|user.*|system.*"
    
    def can_handle(self, event_data: Dict[str, Any]) -> bool:
        """Check if this handler can process the given event.
        
        Args:
            event_data: Event data dictionary
            
        Returns:
            bool: True if this handler can process the event
        """
        event_type = event_data.get("event_type", "")
        
        # Check if event type matches any of the patterns
        patterns = ["task.", "user.", "system."]
        return any(event_type.startswith(pattern) for pattern in patterns)
    
    def handle(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process the generic system event.
        
        Args:
            event_data: Event data dictionary
            
        Returns:
            Dict[str, Any]: Processing result
        """
        try:
            event_type = event_data.get("event_type")
            data = event_data.get("data", {})
            
            logger.info(f"📨 Processing generic event '{event_type}'")
            
            # Route the event based on its prefix
            if event_type.startswith("task."):
                result = self._handle_task_event(event_type, data)
            elif event_type.startswith("user."):
                result = self._handle_user_event(event_type, data)
            elif event_type.startswith("system."):
                result = self._handle_system_event(event_type, data)
            else:
                result = self._handle_unknown_generic_event(event_type, data)
            
            return self._create_success_response(
                event_data=event_data,
                result=result,
                message=f"Successfully processed generic event '{event_type}'"
            )
            
        except Exception as e:
            logger.error(f"Failed to handle generic event: {e}")
            return self._create_error_response(
                event_data=event_data,
                error=e,
                message=f"Generic event processing failed: {e}"
            )
    
    def _handle_task_event(self, event_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle task-related events.
        
        Args:
            event_type: The specific task event type
            data: Event data
            
        Returns:
            Dict[str, Any]: Processing result
        """
        logger.info(f"Processing task event: {event_type}")
        
        # Route to listening agents if needed
        result = self._route_to_listening_agents(event_type, data)
        
        return {
            "event_category": "task",
            "routing_result": result,
            "processed_event": event_type
        }
    
    def _handle_user_event(self, event_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle user-related events.
        
        Args:
            event_type: The specific user event type
            data: Event data
            
        Returns:
            Dict[str, Any]: Processing result
        """
        logger.info(f"Processing user event: {event_type}")
        
        # Route to listening agents if needed
        result = self._route_to_listening_agents(event_type, data)
        
        return {
            "event_category": "user",
            "routing_result": result,
            "processed_event": event_type
        }
    
    def _handle_system_event(self, event_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle system-related events.
        
        Args:
            event_type: The specific system event type
            data: Event data
            
        Returns:
            Dict[str, Any]: Processing result
        """
        logger.info(f"Processing system event: {event_type}")
        
        # Route to listening agents if needed
        result = self._route_to_listening_agents(event_type, data)
        
        return {
            "event_category": "system",
            "routing_result": result,
            "processed_event": event_type
        }
    
    def _handle_unknown_generic_event(self, event_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle unknown generic events.
        
        Args:
            event_type: The event type
            data: Event data
            
        Returns:
            Dict[str, Any]: Processing result
        """
        logger.warning(f"Processing unknown generic event: {event_type}")
        
        return {
            "event_category": "unknown_generic",
            "routing_result": "no_routing_configured",
            "processed_event": event_type
        }
    
    def _route_to_listening_agents(self, event_type: str, data: Dict[str, Any]) -> str:
        """Route event to listening agents.
        
        This method implements the Interface Segregation Principle by
        providing a specific interface for agent routing.
        
        Args:
            event_type: Event type to route
            data: Event data
            
        Returns:
            str: Routing result description
        """
        # TODO: Implement actual agent routing logic
        # This would involve:
        # 1. Finding agents configured to listen for this event type
        # 2. Sending the event to each listening agent
        # 3. Collecting and aggregating responses
        
        logger.info(f"Routing event '{event_type}' to listening agents")
        
        return "agent_routing_not_implemented"