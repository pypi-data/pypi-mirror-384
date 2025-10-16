"""Custom event handler for application-specific events following SOLID principles."""

from typing import Dict, Any

from .base import BaseEventHandler
from ...utils.logging import get_logger

logger = get_logger(__name__)


class CustomEventHandler(BaseEventHandler):
    """Handler for custom application events.
    
    This class follows the Single Responsibility Principle by handling
    only custom application-specific events that don't fit other categories.
    It also follows the Open/Closed Principle by being extensible for
    new custom event types without modification.
    """
    
    @property
    def event_type(self) -> str:
        """Return the event type pattern this handler processes."""
        return "custom.*"
    
    def can_handle(self, event_data: Dict[str, Any]) -> bool:
        """Check if this handler can process the given event.
        
        Args:
            event_data: Event data dictionary
            
        Returns:
            bool: True if this handler can process the event
        """
        event_type = event_data.get("event_type", "")
        
        # Handle any event that doesn't match other patterns
        # This serves as a fallback handler following the Chain of Responsibility pattern
        known_patterns = ["agent_call", "execute_tool", "task.", "user.", "system."]
        
        # If it doesn't match any known pattern, treat it as custom
        return not any(
            event_type == pattern or event_type.startswith(pattern) 
            for pattern in known_patterns
        )
    
    def handle(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process the custom event.
        
        Args:
            event_data: Event data dictionary
            
        Returns:
            Dict[str, Any]: Processing result
        """
        try:
            event_type = event_data.get("event_type")
            data = event_data.get("data", {})
            
            logger.info(f"🔧 Processing custom event '{event_type}'")
            
            # Process the custom event
            result = self._process_custom_event(event_type, data)
            
            return self._create_success_response(
                event_data=event_data,
                result=result,
                message=f"Successfully processed custom event '{event_type}'"
            )
            
        except Exception as e:
            logger.error(f"Failed to handle custom event: {e}")
            return self._create_error_response(
                event_data=event_data,
                error=e,
                message=f"Custom event processing failed: {e}"
            )
    
    def _process_custom_event(self, event_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a custom event based on its type.
        
        This method can be extended to handle specific custom event types
        following the Open/Closed Principle.
        
        Args:
            event_type: The custom event type
            data: Event data
            
        Returns:
            Dict[str, Any]: Processing result
        """
        # Check for specific custom event patterns
        if event_type.startswith("notification."):
            return self._handle_notification_event(event_type, data)
        elif event_type.startswith("workflow."):
            return self._handle_workflow_event(event_type, data)
        elif event_type.startswith("integration."):
            return self._handle_integration_event(event_type, data)
        else:
            return self._handle_generic_custom_event(event_type, data)
    
    def _handle_notification_event(self, event_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle notification-related custom events.
        
        Args:
            event_type: The notification event type
            data: Event data
            
        Returns:
            Dict[str, Any]: Processing result
        """
        logger.info(f"Processing notification event: {event_type}")
        
        # Extract notification details
        recipient = data.get("recipient")
        message = data.get("message")
        channel = data.get("channel", "default")
        
        return {
            "event_category": "notification",
            "recipient": recipient,
            "message": message,
            "channel": channel,
            "status": "acknowledged",
            "note": "Notification processing implementation pending"
        }
    
    def _handle_workflow_event(self, event_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle workflow-related custom events.
        
        Args:
            event_type: The workflow event type
            data: Event data
            
        Returns:
            Dict[str, Any]: Processing result
        """
        logger.info(f"Processing workflow event: {event_type}")
        
        # Extract workflow details
        workflow_id = data.get("workflow_id")
        step = data.get("step")
        status = data.get("status")
        
        return {
            "event_category": "workflow",
            "workflow_id": workflow_id,
            "step": step,
            "status": status,
            "result": "acknowledged",
            "note": "Workflow processing implementation pending"
        }
    
    def _handle_integration_event(self, event_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle integration-related custom events.
        
        Args:
            event_type: The integration event type
            data: Event data
            
        Returns:
            Dict[str, Any]: Processing result
        """
        logger.info(f"Processing integration event: {event_type}")
        
        # Extract integration details
        service = data.get("service")
        action = data.get("action")
        payload = data.get("payload")
        
        return {
            "event_category": "integration",
            "service": service,
            "action": action,
            "payload_size": len(str(payload)) if payload else 0,
            "status": "acknowledged",
            "note": "Integration processing implementation pending"
        }
    
    def _handle_generic_custom_event(self, event_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle generic custom events that don't fit specific categories.
        
        Args:
            event_type: The event type
            data: Event data
            
        Returns:
            Dict[str, Any]: Processing result
        """
        logger.info(f"Processing generic custom event: {event_type}")
        
        return {
            "event_category": "generic_custom",
            "event_type": event_type,
            "data_keys": list(data.keys()) if data else [],
            "status": "acknowledged",
            "note": "Generic custom event acknowledged and logged"
        }