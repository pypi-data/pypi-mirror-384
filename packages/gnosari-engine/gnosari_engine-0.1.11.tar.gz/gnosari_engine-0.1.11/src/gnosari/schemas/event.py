"""Event system schemas for Gnosari AI Teams.

This module defines the core data structures for the event-driven agent system,
including event messages, queue configurations, and agent listener settings.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, validator
from datetime import datetime
import uuid


class QueueConfig(BaseModel):
    """Configuration schema for event queues."""
    
    name: str = Field(description="Queue name")
    priority: int = Field(default=5, ge=1, le=10, description="Queue priority (1=highest)")
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    retry_delay: int = Field(default=60, description="Retry delay in seconds")
    dead_letter_queue: Optional[str] = Field(None, description="Dead letter queue name")
    routing_key: Optional[str] = Field(None, description="Routing key pattern")
    
    @validator('name')
    def validate_queue_name(cls, v):
        """Validate queue name format and length."""
        if not v or len(v) > 50:
            raise ValueError('Queue name must be 1-50 characters')
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Queue name can only contain alphanumeric characters, hyphens, and underscores')
        return v
    
    @validator('routing_key')
    def validate_routing_key(cls, v):
        """Validate routing key pattern."""
        if v and len(v) > 100:
            raise ValueError('Routing key must be less than 100 characters')
        return v


class EventMessage(BaseModel):
    """Base event message schema."""
    
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str = Field(description="Type of event")
    source: str = Field(description="Event source identifier") 
    data: Dict[str, Any] = Field(default_factory=dict, description="Event payload")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Event metadata")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    priority: int = Field(default=5, ge=1, le=10, description="Event priority")
    broadcast: bool = Field(default=False, description="Broadcast to all teams")
    target_teams: Optional[List[str]] = Field(None, description="Specific target teams")
    correlation_id: Optional[str] = Field(None, description="Correlation ID for tracking")
    session: Optional[Dict[str, Any]] = Field(None, description="Session context information")
    
    @validator('event_type')
    def validate_event_type(cls, v):
        """Validate event type format."""
        if not v or len(v) > 100:
            raise ValueError('Event type must be 1-100 characters')
        if not all(c.isalnum() or c in '._-' for c in v):
            raise ValueError('Event type can only contain alphanumeric characters, dots, hyphens, and underscores')
        return v
    
    @validator('source')
    def validate_source(cls, v):
        """Validate source identifier."""
        if not v or len(v) > 100:
            raise ValueError('Source must be 1-100 characters')
        return v
    
    @validator('data')
    def validate_data_size(cls, v):
        """Validate event data payload size."""
        import json
        try:
            serialized = json.dumps(v)
            if len(serialized) > 1024 * 1024:  # 1MB limit
                raise ValueError('Event data payload too large (max 1MB)')
        except (TypeError, ValueError) as e:
            if 'too large' in str(e):
                raise
            raise ValueError('Event data must be JSON serializable')
        return v


class AgentListener(BaseModel):
    """Agent event listener configuration."""
    
    event_types: List[str] = Field(description="Event types to listen for")
    instructions: str = Field(description="Instructions for processing events")
    priority: int = Field(default=5, description="Listener priority")
    filter_expression: Optional[str] = Field(None, description="Event filter expression")
    max_concurrent: int = Field(default=1, ge=1, le=10, description="Max concurrent event processing")
    timeout: int = Field(default=300, ge=30, le=3600, description="Processing timeout in seconds")
    retry_failed: bool = Field(default=True, description="Retry failed event processing")
    
    @validator('event_types')
    def validate_event_types(cls, v):
        """Validate event type patterns."""
        if not v:
            raise ValueError('At least one event type must be specified')
        for event_type in v:
            if not event_type or len(event_type) > 100:
                raise ValueError('Event type must be 1-100 characters')
            if not all(c.isalnum() or c in '._-*' for c in event_type):
                raise ValueError('Event type can only contain alphanumeric characters, dots, hyphens, underscores, and wildcards')
        return v
    
    @validator('instructions')
    def validate_instructions(cls, v):
        """Validate instructions length."""
        if not v.strip() or len(v) > 1000:
            raise ValueError('Instructions must be 1-1000 characters')
        return v.strip()
    
    @validator('filter_expression')
    def validate_filter_expression(cls, v):
        """Validate filter expression syntax."""
        if v:
            # Basic validation for filter expressions
            if len(v) > 200:
                raise ValueError('Filter expression must be less than 200 characters')
            # Additional syntax validation could be added here
        return v


class AgentTrigger(BaseModel):
    """Agent event trigger configuration."""
    
    event_type: str = Field(description="Type of event to trigger")
    instructions: str = Field(description="Instructions for when to trigger this event")
    conditions: str = Field(description="Specific conditions that should trigger this event")
    data_fields: List[str] = Field(default_factory=list, description="Required data fields to include")
    priority: int = Field(default=5, ge=1, le=10, description="Event priority")
    broadcast: bool = Field(default=False, description="Whether to broadcast this event")
    target_teams: Optional[List[str]] = Field(None, description="Specific teams to target")
    
    @validator('event_type')
    def validate_event_type(cls, v):
        """Validate event type format."""
        if not v or len(v) > 100:
            raise ValueError('Event type must be 1-100 characters')
        if not all(c.isalnum() or c in '._-' for c in v):
            raise ValueError('Event type can only contain alphanumeric characters, dots, hyphens, and underscores')
        return v
    
    @validator('instructions')
    def validate_instructions(cls, v):
        """Validate instructions length."""
        if not v.strip() or len(v) > 1000:
            raise ValueError('Instructions must be 1-1000 characters')
        return v.strip()
    
    @validator('conditions')
    def validate_conditions(cls, v):
        """Validate conditions length."""
        if not v.strip() or len(v) > 500:
            raise ValueError('Conditions must be 1-500 characters')
        return v.strip()
    
    @validator('data_fields')
    def validate_data_fields(cls, v):
        """Validate data field names."""
        for field in v:
            if not field or len(field) > 50:
                raise ValueError('Data field names must be 1-50 characters')
            if not field.replace('_', '').isalnum():
                raise ValueError('Data field names can only contain alphanumeric characters and underscores')
        return v


class EventResponse(BaseModel):
    """Response from event processing."""
    
    event_id: str
    agent_name: str
    status: str = Field(description="success, failed, timeout")
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    processing_time: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    @validator('status')
    def validate_status(cls, v):
        """Validate response status."""
        valid_statuses = {'success', 'failed', 'timeout', 'processing', 'queued'}
        if v not in valid_statuses:
            raise ValueError(f'Status must be one of: {valid_statuses}')
        return v
    
    @validator('processing_time')
    def validate_processing_time(cls, v):
        """Validate processing time is non-negative."""
        if v < 0:
            raise ValueError('Processing time cannot be negative')
        return v


class EventConfig(BaseModel):
    """Event system configuration."""
    
    publisher_queue: str = Field(default="gnosari_events", description="Default queue for publishing events")
    default_priority: int = Field(default=5, ge=1, le=10, description="Default event priority")
    enable_broadcasting: bool = Field(default=True, description="Enable event broadcasting")
    correlation_tracking: bool = Field(default=True, description="Enable correlation ID tracking")
    max_event_size: int = Field(default=1048576, description="Maximum event size in bytes")  # 1MB
    
    @validator('publisher_queue')
    def validate_publisher_queue(cls, v):
        """Validate publisher queue name."""
        if not v or len(v) > 50:
            raise ValueError('Publisher queue name must be 1-50 characters')
        return v


class EventSystemError(Exception):
    """Base exception for event system errors."""
    
    def __init__(self, message: str, error_code: str = None, event_id: str = None):
        self.message = message
        self.error_code = error_code
        self.event_id = event_id
        super().__init__(self.message)


class EventProcessingError(EventSystemError):
    """Error during event processing by agent."""
    pass


class QueueConfigurationError(EventSystemError):
    """Error in queue configuration."""
    pass


class EventRoutingError(EventSystemError):
    """Error in event routing and dispatching."""
    pass


# Event Context Schemas for different event types

class AgentCallContext(BaseModel):
    """Context data for agent delegation events."""
    target_agent: str = Field(description="Name of the agent to delegate to")
    message: str = Field(description="Message or task to delegate")
    session_id: Optional[str] = Field(default=None, description="Session identifier")
    team_config: Dict[str, Any] = Field(description="Team configuration")
    
    @validator('target_agent')
    def validate_target_agent(cls, v):
        if not v or len(v) > 100:
            raise ValueError('Target agent name must be 1-100 characters')
        return v
    
    @validator('message')
    def validate_message(cls, v):
        if not v.strip():
            raise ValueError('Message cannot be empty')
        return v.strip()


class ToolExecutionContext(BaseModel):
    """Context data for async tool execution events."""
    tool_name: str = Field(description="Name of the tool to execute")
    tool_module: str = Field(description="Module path of the tool")
    tool_class: str = Field(description="Class name of the tool")
    tool_args: str = Field(description="JSON string of tool arguments")
    tool_init_args: Dict[str, Any] = Field(default_factory=dict, description="Tool initialization arguments")
    context_data: Dict[str, Any] = Field(description="Serialized execution context")
    agent_id: str = Field(description="Agent identifier")
    session_id: Optional[str] = Field(None, description="Session identifier")
    
    @validator('tool_name')
    def validate_tool_name(cls, v):
        if not v or len(v) > 100:
            raise ValueError('Tool name must be 1-100 characters')
        return v
    
    @validator('tool_args')
    def validate_tool_args(cls, v):
        import json
        try:
            json.loads(v)
        except json.JSONDecodeError:
            raise ValueError('Tool args must be valid JSON string')
        return v


class GenericEventContext(BaseModel):
    """Context data for generic events published via event_publisher."""
    source: str = Field(description="Event source identifier")
    priority: int = Field(default=5, ge=1, le=10, description="Event priority")
    broadcast: bool = Field(default=False, description="Broadcast to all teams")
    
    @validator('source')
    def validate_source(cls, v):
        if not v or len(v) > 100:
            raise ValueError('Source must be 1-100 characters')
        return v


class GenericEventContextWithData(BaseModel):
    """Context data for generic events with custom data payload."""
    source: str = Field(description="Event source identifier")
    priority: int = Field(default=5, ge=1, le=10, description="Event priority")
    broadcast: bool = Field(default=False, description="Broadcast to all teams")
    data: Dict[str, Any] = Field(default_factory=dict, description="Event data payload")
    
    @validator('source')
    def validate_source(cls, v):
        if not v or len(v) > 100:
            raise ValueError('Source must be 1-100 characters')
        return v


# Event Type Constants
class EventTypes:
    """Constants for standard event types."""
    AGENT_CALL = "agent_call"
    TOOL_EXECUTION = "execute_tool"
    GENERIC_EVENT = "generic_event"
    TASK_COMPLETED = "task.completed"
    USER_ACTION = "user.action"
    SYSTEM_NOTIFICATION = "system.notification"


# Unified Event Factory
def create_event(event_type: str, context: BaseModel, source: str = "system", 
                priority: int = 5, metadata: Dict[str, Any] = None, 
                session: Dict[str, Any] = None) -> EventMessage:
    """Create a standardized event message.
    
    Args:
        event_type: Type of event (use EventTypes constants)
        context: Event context data (appropriate schema for event type)
        source: Event source identifier
        priority: Event priority (1-10)
        metadata: Additional metadata
        session: Session context information
        
    Returns:
        EventMessage: Standardized event message
    """
    return EventMessage(
        event_type=event_type,
        source=source,
        data=context.model_dump(),
        metadata=metadata or {},
        priority=priority,
        session=session
    )