"""Tool resolution functionality for agents."""

import logging
from typing import List, Dict, Any, Optional

from ...tools import DelegateAgentTool, KnowledgeQueryTool, ToolManager
from ...knowledge import KnowledgeManager


class ToolResolver:
    """Resolves and prepares tools for agent creation."""
    
    def __init__(self, tool_manager: ToolManager, knowledge_manager: Optional[KnowledgeManager] = None, session_id: str = None):
        self.tool_manager = tool_manager
        self.knowledge_manager = knowledge_manager
        self.session_id = session_id
        self.logger = logging.getLogger(__name__)
        self._delegate_tools: Dict[str, DelegateAgentTool] = {}
    
    def resolve_tools_for_agent(
        self, 
        agent_name: str,
        agent_tools: List[str], 
        agent_config: Dict[str, Any],
        team_config: Dict[str, Any]
    ) -> List[Any]:
        """
        Resolve all tools for an agent.
        
        Args:
            agent_name: Name of the agent
            agent_tools: List of tool names/IDs for the agent
            agent_config: Agent-specific configuration
            team_config: Full team configuration
            
        Returns:
            List of OpenAI-compatible tool instances
        """
        openai_tools = []
        
        # Add knowledge query tool if agent has knowledge bases configured
        if self._should_add_knowledge_tool(agent_config):
            knowledge_tool = self._get_or_create_knowledge_tool(agent_name)
            if knowledge_tool:
                openai_tools.append(knowledge_tool)
                self.logger.debug(f"Added knowledge_query tool to agent '{agent_name}'")
            else:
                self.logger.warning(f"Failed to create knowledge_query tool for agent '{agent_name}'")
        
        # Handle delegate_agent tool if delegation is configured
        delegate_tool = self._resolve_delegation_tool(agent_name, agent_config, team_config)
        if delegate_tool:
            openai_tools.append(delegate_tool)
            # Remove from tools list to avoid duplicate processing
            agent_tools = [tool for tool in agent_tools if tool != "delegate_agent"]
        
        # Handle other tools from configuration
        if agent_tools:
            resolved_tools = self._resolve_configured_tools(agent_name, agent_tools)
            openai_tools.extend(resolved_tools)
        
        return openai_tools
    
    def _should_add_knowledge_tool(self, agent_config: Dict[str, Any]) -> bool:
        """Check if agent should have knowledge query tool."""
        if not agent_config:
            return False
        
        knowledge_config = agent_config.get('knowledge')
        if not knowledge_config:
            return False
        
        # Ensure we have a valid knowledge configuration (list of knowledge base names)
        # and not the KnowledgeManager object itself
        if hasattr(knowledge_config, '__class__') and 'KnowledgeManager' in str(knowledge_config.__class__):
            self.logger.warning("agent_config['knowledge'] contains KnowledgeManager object instead of list")
            return self.knowledge_manager is not None
        
        # Normal case: knowledge_config should be a list of knowledge base names
        return self.knowledge_manager is not None
    
    def _get_or_create_knowledge_tool(self, agent_name: str) -> Optional[Any]:
        """Get knowledge query tool from registry or create if needed."""
        # First, try to get the globally registered knowledge tool
        try:
            knowledge_tool_instance = self.tool_manager.registry.get('knowledge_query')
            if knowledge_tool_instance:
                if hasattr(knowledge_tool_instance, 'get_tool'):
                    return knowledge_tool_instance.get_tool()
                else:
                    return knowledge_tool_instance
        except Exception as e:
            self.logger.debug(f"Could not retrieve globally registered knowledge tool: {e}")
        
        # Fallback: create a new knowledge tool if global one not available
        return self._create_knowledge_tool(agent_name)
    
    def _create_knowledge_tool(self, agent_name: str) -> Optional[Any]:
        """Create knowledge query tool as fallback."""
        try:
            knowledge_tool = KnowledgeQueryTool(knowledge_manager=self.knowledge_manager)
            self.logger.info(f"Created fallback knowledge_query tool for agent '{agent_name}'")
            return knowledge_tool.get_tool()
        except Exception as e:
            self.logger.warning(f"Failed to create knowledge tool for agent '{agent_name}': {e}")
            return None
    
    def _resolve_delegation_tool(
        self, 
        agent_name: str, 
        agent_config: Dict[str, Any], 
        team_config: Dict[str, Any]
    ) -> Optional[Any]:
        """Resolve delegation tool if needed."""
        has_delegation = agent_config and agent_config.get('delegation')
        delegate_in_tools = "delegate_agent" in (agent_config.get('tools', []) if agent_config else [])
        
        if not (has_delegation or delegate_in_tools):
            return None
        
        # Check if any delegation rules have async mode
        has_async_delegation = self._has_async_delegation(agent_config)
        
        if has_async_delegation:
            return self._create_async_delegation_tool(agent_name, team_config)
        else:
            return self._create_sync_delegation_tool(agent_name)
    
    def _has_async_delegation(self, agent_config: Dict[str, Any]) -> bool:
        """Check if agent has async delegation rules."""
        if not agent_config or not agent_config.get('delegation'):
            return False
        
        delegation_rules = agent_config.get('delegation', [])
        return any(rule.get('mode') == 'async' for rule in delegation_rules)
    
    def _create_async_delegation_tool(self, agent_name: str, team_config: Dict[str, Any]) -> Any:
        """Create async delegation tool."""
        try:
            # Create base delegation tool
            base_delegate_tool = DelegateAgentTool()
            
            # Store for team dependencies
            self._delegate_tools[agent_name] = base_delegate_tool
            
            # Get the async version of the tool
            async_tool = base_delegate_tool.get_async_tool()
            
            self.logger.info(f"Added ASYNC delegate_agent tool to agent '{agent_name}'")
            return async_tool
            
        except Exception as e:
            self.logger.warning(f"Failed to create async delegation tool for {agent_name}: {e}")
            return self._create_sync_delegation_tool(agent_name)
    
    def _create_sync_delegation_tool(self, agent_name: str) -> Any:
        """Create sync delegation tool."""
        try:
            delegate_tool_instance = DelegateAgentTool()
            self._delegate_tools[agent_name] = delegate_tool_instance
            
            self.logger.info(f"Added SYNC delegate_agent tool to agent '{agent_name}'")
            return delegate_tool_instance.get_tool()
            
        except Exception as e:
            self.logger.warning(f"Failed to create sync delegation tool for {agent_name}: {e}")
            return None
    
    def _resolve_configured_tools(self, agent_name: str, agent_tools: List[str]) -> List[Any]:
        """Resolve tools from configuration."""
        resolved_tools = []
        
        self.logger.debug(f"Processing {len(agent_tools)} tools for agent '{agent_name}': {agent_tools}")
        self.logger.debug(f"Available tools in tool_manager: {list(self.tool_manager.list_available_tools().keys())}")
        
        for tool_name_or_id in agent_tools:
            try:
                tool_instance = self._resolve_single_tool(tool_name_or_id, agent_name)
                if tool_instance:
                    resolved_tools.append(tool_instance)
            except Exception as e:
                self.logger.warning(f"Failed to create tool '{tool_name_or_id}' for agent '{agent_name}': {e}")
        
        return resolved_tools
    
    def _resolve_single_tool(self, tool_name_or_id: str, agent_name: str) -> Optional[Any]:
        """Resolve a single tool from registry."""
        # Get tool instance and configuration from registry
        tool_instance = self.tool_manager.registry.get(tool_name_or_id)
        tool_config = self.tool_manager.registry.get_config(tool_name_or_id)
        
        if not tool_instance or not tool_config:
            self.logger.warning(f"Tool '{tool_name_or_id}' not found in available tools for agent '{agent_name}'")
            self.logger.debug(f"Available tools: {list(self.tool_manager.list_available_tools().keys())}")
            return None
        
        self.logger.debug(f"Found tool for '{tool_name_or_id}': {tool_instance.name}")
        
        # Get OpenAI-compatible tool
        openai_tool = self._get_openai_tool(tool_instance, tool_name_or_id, agent_name)
        
        # Store delegate tools for team dependency setup
        if (isinstance(tool_instance, type(None)) == False and 
            hasattr(tool_instance, '__class__') and 
            tool_instance.__class__.__name__ == "DelegateAgentTool"):
            self._delegate_tools[agent_name] = tool_instance
        
        return openai_tool
    
    def _get_openai_tool(self, tool_instance: Any, tool_name_or_id: str, agent_name: str) -> Any:
        """Get OpenAI-compatible tool from instance."""
        if hasattr(tool_instance, 'get_tool'):
            # Gnosari custom tool - get the FunctionTool
            openai_tool = tool_instance.get_tool()
            self.logger.debug(f"Added Gnosari-style tool '{tool_name_or_id}' via get_tool() method")
        else:
            # OpenAI SDK tool - use directly
            openai_tool = tool_instance
            self.logger.debug(f"Added OpenAI SDK tool '{tool_name_or_id}' directly")
        
        self.logger.info(f"Added OpenAI-compatible tool '{tool_name_or_id}' to agent '{agent_name}'")
        return openai_tool
    
    def get_delegate_tools(self) -> Dict[str, DelegateAgentTool]:
        """Get all delegate tools for team dependency setup."""
        return self._delegate_tools.copy()