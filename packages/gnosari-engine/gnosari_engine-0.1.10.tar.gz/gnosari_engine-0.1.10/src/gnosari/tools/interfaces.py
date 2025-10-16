"""
Tool interfaces for defining different execution capabilities.
"""

import uuid
from abc import ABC, abstractmethod
from typing import Any, Dict
from agents import FunctionTool, RunContextWrapper
from gnosari.tools.base import BaseTool

class AsyncTool(BaseTool):
    """Base class for tools that support asynchronous queue execution.
    
    Tools implementing this interface can be executed asynchronously
    via the queue system, allowing for background processing and
    better resource management.
    
    This class provides common functionality for async execution
    including context serialization and queue message sending.
    """
    
    # Provide default implementation for run method since we use FunctionTool pattern
    async def run(self, input_data: Any) -> Any:
        """Default run implementation - tools use FunctionTool pattern instead."""
        return f"Tool {self.name} executed via FunctionTool interface"
    
    @abstractmethod
    def get_tool(self) -> FunctionTool:
        """Get the synchronous FunctionTool instance.
        
        Returns:
            FunctionTool: Tool for synchronous execution
        """
        pass
    
    @abstractmethod
    def get_async_tool(self) -> FunctionTool:
        """Get the asynchronous FunctionTool instance for queue execution.
        
        Returns:
            FunctionTool: Tool configured for async queue execution
        """
        pass
    
    def supports_async_execution(self) -> bool:
        """Check if this tool supports async execution.
        
        Returns:
            bool: Always True for AsyncTool implementations
        """
        return True
    
    def get_async_metadata(self) -> Dict[str, Any]:
        """Get metadata for async execution configuration.
        
        Returns:
            Dict containing async execution settings like priority,
            timeout, retry configuration, etc.
        """
        return {
            "priority": 5,
            "timeout": 600,  # 10 minutes
            "max_retries": 3,
            "retry_delay": 2
        }
    
    @staticmethod
    def serialize_context(ctx: RunContextWrapper[Any]) -> Dict[str, Any]:
        """Serialize RunContextWrapper to plain dictionary for queue messages.
        
        Args:
            ctx: RunContextWrapper instance to serialize
            
        Returns:
            Dict containing serialized context data
        """
        return {
            'context_wrapper': {
                'context': {
                    'original_config': ctx.context.original_config if ctx.context else None,
                    'team': None,  # Can't serialize team object, will be rebuilt
                    'session_id': ctx.context.session_id if ctx.context else None,
                    'session_context': ctx.context.session_context if ctx.context else {}
                },
                'agent_id': getattr(ctx, 'agent_id', 'Unknown'),
                'session_id': getattr(ctx, 'session_id', None)
            }
        }
    
    def send_async_message(self, 
                          task_id: str,
                          tool_module: str,
                          tool_class: str,
                          tool_args: str,
                          context: RunContextWrapper[Any],
                          tool_init_args: Dict[str, Any] = None,
                          priority: int = None) -> str:
        """Send async execution message to queue using unified event system.
        
        Args:
            task_id: Unique task identifier
            tool_module: Module path of the tool class
            tool_class: Class name of the tool
            tool_args: JSON string of tool execution arguments
            context: RunContextWrapper with execution context
            tool_init_args: Arguments for tool initialization
            priority: Task priority (uses get_async_metadata if not provided)
            
        Returns:
            str: Message ID
        """
        # Import here to avoid circular imports
        from ..schemas.event import EventTypes, ToolExecutionContext
        from ..utils.event_sender import EventSender
        
        # Get metadata for priority if not provided
        if priority is None:
            metadata = self.get_async_metadata()
            priority = metadata.get("priority", 5)
        
        # Serialize context
        context_data = self.serialize_context(context)
        
        # Get session info
        session_id = context.context.session_id if context.context else None
        agent_id = getattr(context, 'agent_id', 'Unknown')
        
        # Create tool execution context
        tool_context = ToolExecutionContext(
            tool_name=self.__class__.__name__.lower().replace('tool', ''),
            tool_module=tool_module,
            tool_class=tool_class,
            tool_args=tool_args,
            tool_init_args=tool_init_args or {},
            context_data=context_data,
            agent_id=agent_id,
            session_id=session_id
        )
        
        # Send via unified event system
        result = EventSender.create_and_send_event(
            event_type=EventTypes.TOOL_EXECUTION,
            context_data=tool_context,
            source=f"async_tool_{self.__class__.__name__}",
            priority=priority,
            metadata={"task_id": task_id, "tool_name": self.name},
            execution_context=context
        )
        
        return result.get("message_id", task_id)
    
    def format_async_response(self, 
                             task_id: str, 
                             message_id: str, 
                             target_name: str, 
                             session_id: str = None) -> str:
        """Format standard async response message.
        
        Args:
            task_id: Task identifier
            message_id: Queue message identifier
            target_name: Name of target (agent, service, etc.)
            session_id: Session identifier
            
        Returns:
            str: Formatted response message
        """
        tool_name = self.__class__.__name__
        return (f"✅ {tool_name} task queued for async execution\n"
                f"Task ID: {task_id}\n"
                f"Message ID: {message_id}\n"
                f"Target: {target_name}\n"
                f"Session: {session_id or 'None'}\n\n"
                f"The task will be processed by the next available worker.")


class SyncTool(BaseTool):
    """Interface for tools that only support synchronous execution.
    
    Tools implementing this interface are executed directly without
    queue processing.
    """
    
    # Provide default implementation for run method since we use FunctionTool pattern
    async def run(self, input_data: Any) -> Any:
        """Default run implementation - tools use FunctionTool pattern instead."""
        return f"Tool {self.name} executed via FunctionTool interface"
    
    @abstractmethod
    def get_tool(self) -> FunctionTool:
        """Get the FunctionTool instance.
        
        Returns:
            FunctionTool: Tool for synchronous execution
        """
        pass
    
    def supports_async_execution(self) -> bool:
        """Check if this tool supports async execution.
        
        Returns:
            bool: Always False for sync-only tools
        """
        return False