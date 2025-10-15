"""Execute tool event handler following SOLID principles."""

import importlib
from typing import Dict, Any

from .base import BaseEventHandler
from ...utils.logging import get_logger

logger = get_logger(__name__)


class ExecuteToolEventHandler(BaseEventHandler):
    """Handler for execute_tool events.
    
    This class follows the Single Responsibility Principle by handling
    only tool execution events.
    """
    
    @property
    def event_type(self) -> str:
        """Return the event type this handler processes."""
        return "execute_tool"
    
    def can_handle(self, event_data: Dict[str, Any]) -> bool:
        """Check if this handler can process the given event.
        
        Args:
            event_data: Event data dictionary
            
        Returns:
            bool: True if this handler can process the event
        """
        event_type = event_data.get("event_type")
        if event_type != self.event_type:
            return False
            
        # Check required fields are present
        data = event_data.get("data", {})
        required_fields = ["tool_name"]
        return all(field in data for field in required_fields)
    
    def handle(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process the tool execution event.
        
        Args:
            event_data: Event data dictionary
            
        Returns:
            Dict[str, Any]: Processing result
        """
        try:
            data = event_data.get("data", {})
            tool_name = data.get("tool_name")
            tool_module = data.get("tool_module")
            tool_class = data.get("tool_class")
            tool_args = data.get("tool_args", {})
            
            logger.info(f"⚙️ Processing tool execution for '{tool_name}'")
            
            # Execute the tool
            result = self._execute_tool(
                tool_name=tool_name,
                tool_module=tool_module,
                tool_class=tool_class,
                tool_args=tool_args
            )
            
            return self._create_success_response(
                event_data=event_data,
                result=result,
                message=f"Successfully executed tool '{tool_name}'"
            )
            
        except Exception as e:
            logger.error(f"Failed to handle tool execution: {e}")
            return self._create_error_response(
                event_data=event_data,
                error=e,
                message=f"Tool execution failed: {e}"
            )
    
    def _execute_tool(self, tool_name: str, tool_module: str = None, 
                      tool_class: str = None, tool_args: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute the actual tool.
        
        Args:
            tool_name: Name of the tool to execute
            tool_module: Module path for dynamic import
            tool_class: Class name for instantiation
            tool_args: Arguments to pass to the tool
            
        Returns:
            Dict[str, Any]: Tool execution result
        """
        tool_args = tool_args or {}
        
        if tool_module and tool_class:
            # Dynamic tool execution
            result = self._execute_dynamic_tool(tool_module, tool_class, tool_args)
        else:
            # Built-in tool execution or fallback
            result = self._execute_builtin_tool(tool_name, tool_args)
        
        return {
            "tool_name": tool_name,
            "result": result,
            "status": "completed"
        }
    
    def _execute_dynamic_tool(self, module_path: str, class_name: str, args: Dict[str, Any]) -> Any:
        """Execute a dynamically imported tool.
        
        Args:
            module_path: Python module path
            class_name: Tool class name
            args: Tool arguments
            
        Returns:
            Any: Tool execution result
        """
        try:
            # Import the module
            module = importlib.import_module(module_path)
            
            # Get the tool class
            tool_class = getattr(module, class_name)
            
            # Instantiate the tool
            tool_instance = tool_class()
            
            # Execute the tool
            if hasattr(tool_instance, 'run'):
                return tool_instance.run(**args)
            elif hasattr(tool_instance, 'execute'):
                return tool_instance.execute(**args)
            else:
                raise AttributeError(f"Tool class {class_name} has no 'run' or 'execute' method")
                
        except ImportError as e:
            raise Exception(f"Failed to import tool module '{module_path}': {e}")
        except AttributeError as e:
            raise Exception(f"Failed to find tool class '{class_name}': {e}")
        except Exception as e:
            raise Exception(f"Failed to execute tool: {e}")
    
    def _execute_builtin_tool(self, tool_name: str, args: Dict[str, Any]) -> Any:
        """Execute a built-in tool.
        
        Args:
            tool_name: Tool name
            args: Tool arguments
            
        Returns:
            Any: Tool execution result
        """
        # For now, return a placeholder result
        # This could be extended to handle specific built-in tools
        logger.info(f"Executing built-in tool '{tool_name}' with args: {args}")
        
        return {
            "message": f"Built-in tool '{tool_name}' executed",
            "args": args,
            "note": "Built-in tool execution implementation pending"
        }