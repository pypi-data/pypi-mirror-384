"""
Base tool classes and interfaces for Gnosari AI Teams.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, TypeVar, Optional, Union
from pydantic import BaseModel
from agents import FunctionTool

InputSchema = TypeVar('InputSchema', bound=BaseModel)
OutputSchema = TypeVar('OutputSchema', bound=BaseModel)


class BaseTool(ABC, Generic[InputSchema, OutputSchema]):
    """
    Base class for all Gnosari tools.
    
    This class provides a standard interface for creating tools that can be
    used with both the OpenAI Agents SDK and custom Gnosari functionality.
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        input_schema: type[InputSchema],
        output_schema: Optional[type[OutputSchema]] = None
    ):
        """
        Initialize the base tool.
        
        Args:
            name: Tool name
            description: Tool description
            input_schema: Pydantic model for input validation
            output_schema: Optional Pydantic model for output validation
        """
        self.name = name
        self.description = description
        self.input_schema = input_schema
        self.output_schema = output_schema
        
    @abstractmethod
    async def run(self, input_data: InputSchema) -> Any:
        """
        Execute the tool with the given input.
        
        Args:
            input_data: Validated input data
            
        Returns:
            Tool execution result
        """
        pass
    
    def get_tool(self) -> FunctionTool:
        """
        Get an OpenAI Agents SDK compatible FunctionTool.
        
        Returns:
            FunctionTool instance for use with OpenAI Agents SDK
        """
        from agents import RunContextWrapper
        
        async def invoke_wrapper(ctx: RunContextWrapper[Any], args: str) -> str:
            """Wrapper function for OpenAI Agents SDK integration."""
            import json
            
            # Parse the arguments
            args_dict = json.loads(args)
            
            # Validate input using Pydantic schema
            input_data = self.input_schema(**args_dict)
            
            # Execute the tool
            result = await self.run(input_data)
            
            # Return result as string (OpenAI Agents SDK requirement)
            if isinstance(result, str):
                return result
            elif isinstance(result, dict):
                return json.dumps(result)
            else:
                return str(result)
        
        return FunctionTool(
            name=self.name,
            description=self.description,
            params_json_schema=self.input_schema.model_json_schema(),
            on_invoke_tool=invoke_wrapper
        )
    
    @staticmethod
    def get_session_team_id(session_context: Optional[Union[Dict[str, Any], 'SessionContext']]) -> Optional[str]:
        """Safely extract team_id from session context.
        
        Args:
            session_context: Session context dictionary or SessionContext object
            
        Returns:
            Team ID if present, None otherwise
        """
        if session_context:
            if hasattr(session_context, 'team_id'):  # SessionContext object
                return session_context.team_id
            elif isinstance(session_context, dict):  # Dict
                return session_context.get('team_id')
        return None
    
    @staticmethod
    def get_session_agent_id(session_context: Optional[Union[Dict[str, Any], 'SessionContext']]) -> Optional[str]:
        """Safely extract agent_id from session context.
        
        Args:
            session_context: Session context dictionary or SessionContext object
            
        Returns:
            Agent ID if present, None otherwise
        """
        if session_context:
            if hasattr(session_context, 'agent_id'):  # SessionContext object
                return session_context.agent_id
            elif isinstance(session_context, dict):  # Dict
                return session_context.get('agent_id')
        return None
    
    @staticmethod
    def get_session_account_id(session_context: Optional[Union[Dict[str, Any], 'SessionContext']]) -> Optional[int]:
        """Safely extract account_id from session context.
        
        Args:
            session_context: Session context dictionary or SessionContext object
            
        Returns:
            Account ID if present, None otherwise
        """
        if session_context:
            if hasattr(session_context, 'account_id'):  # SessionContext object
                return session_context.account_id
            elif isinstance(session_context, dict):  # Dict
                return session_context.get('account_id')
        return None
    
    @staticmethod
    def validate_session_context(session_context: Optional[Dict[str, Any]]) -> Optional['SessionContext']:
        """Validate and convert session context dict to SessionContext object.
        
        Args:
            session_context: Session context dictionary
            
        Returns:
            SessionContext object if validation succeeds, None otherwise
        """
        if not session_context or not isinstance(session_context, dict):
            return None
        
        try:
            # Import here to avoid circular imports
            from ..schemas import SessionContext
            return SessionContext(**session_context)
        except Exception:
            return None
    
    @staticmethod
    def get_session_context_from_ctx(ctx) -> Optional['SessionContext']:
        """Get SessionContext object from RunContextWrapper.
        
        Args:
            ctx: RunContextWrapper from tool invocation
            
        Returns:
            SessionContext object if available, None otherwise
        """
        try:
            # Import here to avoid circular imports
            from ..schemas import SessionContext
            
            # The context parameter from Runner.run(context=context) becomes available as ctx itself
            # Try to treat ctx directly as SessionContext if it has the right attributes
            if isinstance(ctx, SessionContext):
                return ctx
            
            # Try to treat ctx directly as SessionContext if it has session-like attributes
            if hasattr(ctx, 'session_id') or hasattr(ctx, 'team_id') or hasattr(ctx, 'agent_id'):
                try:
                    session_dict = {}
                    for attr in ['session_id', 'team_id', 'agent_id', 'team_identifier', 'agent_identifier', 'account_id', 'original_config', 'metadata']:
                        if hasattr(ctx, attr):
                            session_dict[attr] = getattr(ctx, attr)
                    if session_dict:
                        return SessionContext(**session_dict)
                except Exception:
                    pass
            
            # Check if ctx has a property that contains the session context
            if hasattr(ctx, 'context') and ctx.context:
                # Try direct access to context as SessionContext
                if isinstance(ctx.context, SessionContext):
                    return ctx.context
                
                # Try to extract session context from various possible attributes
                try:
                    if hasattr(ctx.context, 'get_session_context_obj'):
                        result = ctx.context.get_session_context_obj()
                        if result is not None:
                            return result
                except (AttributeError, Exception):
                    pass
                    
                try:
                    if hasattr(ctx.context, '_session_context_obj'):
                        result = ctx.context._session_context_obj
                        if result is not None:
                            return result
                except (AttributeError, Exception):
                    pass
                    
                # Fallback to converting from dict
                try:
                    if hasattr(ctx.context, 'session_context'):
                        return BaseTool.validate_session_context(ctx.context.session_context)
                except (AttributeError, Exception):
                    pass
                    
                # Try to build SessionContext from ctx.context attributes
                try:
                    session_dict = {}
                    for attr in ['session_id', 'team_id', 'agent_id', 'team_identifier', 'agent_identifier', 'account_id', 'original_config', 'metadata']:
                        if hasattr(ctx.context, attr):
                            session_dict[attr] = getattr(ctx.context, attr)
                    if session_dict:
                        return SessionContext(**session_dict)
                except Exception:
                    pass
                    
        except Exception:
            pass
        return None


class SimpleStringTool(BaseTool[BaseModel, str]):
    """
    Simplified base class for tools that take string input and return string output.
    """
    
    def __init__(self, name: str, description: str):
        # Create a simple string input schema
        class StringInput(BaseModel):
            input: str
            
        super().__init__(name, description, StringInput)
    
    @abstractmethod
    async def run_simple(self, input_str: str) -> str:
        """
        Execute the tool with string input.
        
        Args:
            input_str: Input string
            
        Returns:
            Output string
        """
        pass
    
    async def run(self, input_data: BaseModel) -> str:
        """Implementation of base run method."""
        return await self.run_simple(input_data.input)


class ToolRegistry:
    """
    Registry for managing available tools.
    """
    
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}  # indexed by tool name
        self._tool_configs: Dict[str, Dict[str, Any]] = {}  # indexed by tool name
        self._id_to_name: Dict[str, str] = {}  # maps tool ID to tool name
    
    def register(self, tool: BaseTool, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Register a tool.
        
        Args:
            tool: Tool instance to register
            config: Optional configuration for the tool
        """
        # Override tool name and description from config if provided
        if config:
            yaml_name = config.get('name')
            yaml_description = config.get('description')
            
            # Update tool's name and description from YAML if provided
            if yaml_name:
                tool.name = yaml_name
            if yaml_description:
                tool.description = yaml_description
            
            # Store config
            self._tool_configs[tool.name] = config
            
            # Map tool ID to tool name if ID is provided
            tool_id = config.get('id')
            if tool_id:
                self._id_to_name[tool_id] = tool.name
        
        # Register tool with potentially updated name
        self._tools[tool.name] = tool
    
    def get(self, name_or_id: str) -> Optional[BaseTool]:
        """
        Get a tool by name or ID.
        
        Args:
            name_or_id: Tool name or ID
            
        Returns:
            Tool instance or None if not found
        """
        # First try direct name lookup
        tool = self._tools.get(name_or_id)
        if tool:
            return tool
        
        # If not found, try ID lookup
        tool_name = self._id_to_name.get(name_or_id)
        if tool_name:
            return self._tools.get(tool_name)
        
        return None
    
    def get_config(self, name_or_id: str) -> Optional[Dict[str, Any]]:
        """
        Get tool configuration by name or ID.
        
        Args:
            name_or_id: Tool name or ID
            
        Returns:
            Tool configuration or None if not found
        """
        # First try direct name lookup
        config = self._tool_configs.get(name_or_id)
        if config:
            return config
        
        # If not found, try ID lookup
        tool_name = self._id_to_name.get(name_or_id)
        if tool_name:
            return self._tool_configs.get(tool_name)
        
        return None
    
    def list_tools(self) -> Dict[str, str]:
        """
        List all registered tools.
        
        Returns:
            Dictionary mapping tool names to descriptions
        """
        return {name: tool.description for name, tool in self._tools.items()}
    
    def unregister(self, name_or_id: str) -> bool:
        """
        Unregister a tool by name or ID.
        
        Args:
            name_or_id: Tool name or ID to unregister
            
        Returns:
            True if tool was found and removed, False otherwise
        """
        # Get the actual tool name
        tool_name = name_or_id
        if name_or_id in self._id_to_name:
            tool_name = self._id_to_name[name_or_id]
        
        if tool_name in self._tools:
            # Remove tool and config
            del self._tools[tool_name]
            config = self._tool_configs.pop(tool_name, None)
            
            # Remove ID mapping if it exists
            if config and config.get('id'):
                self._id_to_name.pop(config['id'], None)
            
            return True
        return False
    
    def clear(self) -> None:
        """Clear all registered tools."""
        self._tools.clear()
        self._tool_configs.clear()
        self._id_to_name.clear()


# Global tool registry instance
tool_registry = ToolRegistry()