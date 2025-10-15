"""Base classes for event handlers following SOLID principles."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Type, Optional
import logging
from datetime import datetime

from ...utils.logging import get_logger

logger = get_logger(__name__)


class BaseEventHandler(ABC):
    """Abstract base class for all event handlers.
    
    This class enforces the Single Responsibility Principle by ensuring
    each handler is responsible for one event type only.
    """
    
    @property
    @abstractmethod
    def event_type(self) -> str:
        """Return the event type this handler processes."""
        pass
    
    @abstractmethod
    def can_handle(self, event_data: Dict[str, Any]) -> bool:
        """Check if this handler can process the given event.
        
        Args:
            event_data: Event data dictionary
            
        Returns:
            bool: True if this handler can process the event
        """
        pass
    
    @abstractmethod
    def handle(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process the event and return the result.
        
        Args:
            event_data: Event data dictionary
            
        Returns:
            Dict[str, Any]: Processing result
        """
        pass
    
    def _create_success_response(self, event_data: Dict[str, Any], result: Any = None, message: str = None) -> Dict[str, Any]:
        """Create a standardized success response.
        
        Args:
            event_data: Original event data
            result: Processing result
            message: Success message
            
        Returns:
            Dict[str, Any]: Success response
        """
        return {
            "status": "success",
            "event_id": event_data.get("event_id"),
            "event_type": event_data.get("event_type"),
            "result": result,
            "processed_at": datetime.utcnow().isoformat(),
            "message": message or f"Successfully processed {self.event_type} event"
        }
    
    def _create_error_response(self, event_data: Dict[str, Any], error: Exception, message: str = None) -> Dict[str, Any]:
        """Create a standardized error response.
        
        Args:
            event_data: Original event data
            error: Exception that occurred
            message: Error message
            
        Returns:
            Dict[str, Any]: Error response
        """
        return {
            "status": "failed",
            "event_id": event_data.get("event_id"),
            "event_type": event_data.get("event_type"),
            "error": str(error),
            "processed_at": datetime.utcnow().isoformat(),
            "message": message or f"Failed to process {self.event_type} event: {error}"
        }


class EventHandlerRegistry:
    """Registry for event handlers following the Open/Closed Principle.
    
    New event handlers can be added without modifying existing code.
    """
    
    def __init__(self):
        self._handlers: Dict[str, BaseEventHandler] = {}
        self._pattern_handlers: Dict[str, BaseEventHandler] = {}
    
    def register_handler(self, handler: BaseEventHandler) -> None:
        """Register an event handler.
        
        Args:
            handler: Event handler instance to register
        """
        event_type = handler.event_type
        
        # Check if it's a pattern-based handler (contains wildcards)
        if "*" in event_type or event_type.endswith("."):
            self._pattern_handlers[event_type] = handler
            logger.info(f"Registered pattern handler for: {event_type}")
        else:
            self._handlers[event_type] = handler
            logger.info(f"Registered handler for: {event_type}")
    
    def get_handler(self, event_data: Dict[str, Any]) -> Optional[BaseEventHandler]:
        """Get the appropriate handler for an event.
        
        Args:
            event_data: Event data dictionary
            
        Returns:
            Optional[BaseEventHandler]: Handler if found, None otherwise
        """
        event_type = event_data.get("event_type", "unknown")
        
        # Try exact match first
        if event_type in self._handlers:
            handler = self._handlers[event_type]
            if handler.can_handle(event_data):
                return handler
        
        # Try pattern matches
        for pattern, handler in self._pattern_handlers.items():
            if self._matches_pattern(event_type, pattern) and handler.can_handle(event_data):
                return handler
        
        return None
    
    def _matches_pattern(self, event_type: str, pattern: str) -> bool:
        """Check if an event type matches a pattern.
        
        Args:
            event_type: Event type to check
            pattern: Pattern to match against
            
        Returns:
            bool: True if matches
        """
        if pattern.endswith("*"):
            prefix = pattern[:-1]
            return event_type.startswith(prefix)
        elif pattern.endswith("."):
            prefix = pattern
            return event_type.startswith(prefix)
        else:
            return event_type == pattern
    
    def list_handlers(self) -> Dict[str, str]:
        """List all registered handlers.
        
        Returns:
            Dict[str, str]: Mapping of event types to handler class names
        """
        result = {}
        
        for event_type, handler in self._handlers.items():
            result[event_type] = handler.__class__.__name__
        
        for pattern, handler in self._pattern_handlers.items():
            result[pattern] = handler.__class__.__name__
        
        return result