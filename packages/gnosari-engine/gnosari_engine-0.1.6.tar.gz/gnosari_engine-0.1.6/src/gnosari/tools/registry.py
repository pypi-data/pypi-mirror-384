"""
Tool registration and discovery system for Gnosari AI Teams.
"""

import importlib
import logging
from typing import Any, Dict, List, Optional, Type
from pathlib import Path

from .base import tool_registry
from .interfaces import AsyncTool, SyncTool


class ToolLoader:
    """
    Tool loader for discovering and loading tools from various sources.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._loaded_modules = set()
    
    def load_builtin_tools(self) -> None:
        """Load all built-in tools from the builtin package."""
        # Tools are now loaded dynamically from YAML configuration
        # No need to hardcode them here since each tool is explicitly 
        # referenced in the team configuration with module/class info
        self.logger.debug("Builtin tools will be loaded dynamically from team configuration")
    
    def _load_builtin_tool(self, tool_name: str) -> None:
        """Load a specific builtin tool."""
        module_path = f"gnosari.tools.builtin.{tool_name}"
        
        if module_path in self._loaded_modules:
            return
            
        try:
            module = importlib.import_module(module_path)
            self._loaded_modules.add(module_path)
            self.logger.debug(f"Loaded builtin tool module: {module_path}")
        except ImportError as e:
            self.logger.warning(f"Could not import builtin tool module {module_path}: {e}")
    
    def load_tool_from_config(self, tool_config: Dict[str, Any]) -> Optional[Any]:
        """
        Load a tool from configuration.
        
        Args:
            tool_config: Tool configuration dictionary
            
        Returns:
            Loaded tool instance or None if loading failed
        """
        tool_name = tool_config.get('name')
        module_name = tool_config.get('module')
        class_name = tool_config.get('class_name') or tool_config.get('class')  # Support both class_name and class fields
        args = tool_config.get('args', {})
        mode = tool_config.get('mode', 'sync')  # Default to sync execution
        
        if not all([tool_name, module_name, class_name]):
            self.logger.error(f"Invalid tool config: {tool_config}")
            return None
        
        try:
            # Import the module
            module = importlib.import_module(module_name)
            
            # Get the tool class
            tool_class = getattr(module, class_name)
            
            # Create tool instance
            if args and args != "pass":
                tool_instance = tool_class(**args)
            else:
                tool_instance = tool_class()
            
            # All tools must implement proper interfaces (AsyncTool or SyncTool)
            if not isinstance(tool_instance, (AsyncTool, SyncTool)):
                self.logger.error(f"Tool '{tool_name}' must implement AsyncTool or SyncTool interface")
                return None
                
            # For async mode, tools will use get_async_tool() method when needed
            # No need for adapter - the tool registry will call the appropriate method
            
            return tool_instance
            
        except Exception as e:
            self.logger.error(f"Failed to load tool '{tool_name}' from {module_name}.{class_name}: {e}")
            return None
    
# Removed legacy tool adaptation - all tools must implement AsyncTool or SyncTool interfaces
    
    
    def discover_tools_in_directory(self, directory: Path) -> List[str]:
        """
        Discover available tools in a directory.
        
        Args:
            directory: Directory to search for tools
            
        Returns:
            List of discovered tool module names
        """
        discovered = []
        
        if not directory.exists():
            return discovered
        
        for file_path in directory.glob("*.py"):
            if file_path.name.startswith("_"):
                continue
                
            module_name = file_path.stem
            discovered.append(module_name)
        
        return discovered


# Removed legacy adapter classes - all tools use AsyncTool or SyncTool interfaces directly


class ToolManager:
    """
    High-level tool manager that combines loading and registry functionality.
    """
    
    def __init__(self):
        self.loader = ToolLoader()
        self.registry = tool_registry
        self.logger = logging.getLogger(__name__)
    
    def initialize(self) -> None:
        """Initialize the tool manager."""
        # Tools are loaded dynamically from team configuration
        self.logger.info("Tool manager initialized - tools will be loaded from configuration")
    
    def load_tools_from_config(self, config: Dict[str, Any], team_config: Dict[str, Any] = None) -> None:
        """
        Load tools from team configuration.
        
        Args:
            config: Team configuration dictionary
            team_config: Full team configuration for async tools
        """
        tools_config = config.get('tools', [])
        
        for tool_config in tools_config:
            # Skip MCP servers (they have 'url' or 'command')
            if tool_config.get('url') or tool_config.get('command'):
                continue
            
            tool = self.loader.load_tool_from_config(tool_config)
            if tool:
                self.registry.register(tool, tool_config)
                self.logger.info(f"Registered tool: {tool.name}")
    
    def get_tool(self, name: str) -> Optional[Any]:
        """Get a tool by name."""
        return self.registry.get(name)
    
    def list_available_tools(self) -> Dict[str, str]:
        """List all available tools."""
        return self.registry.list_tools()
    
    def get_openai_tools(self, tool_names: List[str]) -> List[Any]:
        """
        Get OpenAI Agents SDK compatible tools.
        
        Args:
            tool_names: List of tool names to get
            
        Returns:
            List of OpenAI compatible tool instances
        """
        openai_tools = []
        
        for tool_name in tool_names:
            tool = self.registry.get(tool_name)
            if tool:
                try:
                    openai_tool = tool.get_tool()
                    openai_tools.append(openai_tool)
                except Exception as e:
                    self.logger.error(f"Failed to get OpenAI tool for '{tool_name}': {e}")
            else:
                self.logger.warning(f"Tool '{tool_name}' not found in registry")
        
        return openai_tools
    
    def tool_supports_async(self, tool_name: str) -> bool:
        """
        Check if a tool supports async execution.
        
        Args:
            tool_name: Name of the tool to check
            
        Returns:
            bool: True if tool supports async execution
        """
        tool = self.registry.get(tool_name)
        if not tool:
            return False
        
        return isinstance(tool, AsyncTool)
    
    def get_async_metadata(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        Get async execution metadata for a tool.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Async metadata dict or None if tool doesn't support async
        """
        tool = self.registry.get(tool_name)
        if not tool:
            return None
        
        if isinstance(tool, AsyncTool):
            return tool.get_async_metadata()
        
        return None


# Global tool manager instance
tool_manager = ToolManager()