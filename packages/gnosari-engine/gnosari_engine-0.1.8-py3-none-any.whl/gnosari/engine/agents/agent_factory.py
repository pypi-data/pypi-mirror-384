"""Agent factory for creating OpenAI SDK agents."""

import logging
from typing import Dict, Any, List, Optional, Callable
from agents import Agent
from agents.agent import ModelSettings
from openai.types.chat import ChatCompletionReasoningEffort

from ...prompts import build_agent_system_prompt
from ...providers import setup_provider_for_model
from .tool_resolver import ToolResolver
from ..mcp.server_registry import MCPServerRegistry


class AgentFactory:
    """Factory for creating OpenAI SDK agents with proper configuration."""
    
    def __init__(
        self, 
        tool_resolver: ToolResolver,
        mcp_registry: MCPServerRegistry,
        default_model: str = "gpt-4o",
        default_temperature: float = 1.0,
        session_id: str = None
    ):
        self.tool_resolver = tool_resolver
        self.mcp_registry = mcp_registry
        self.default_model = default_model
        self.default_temperature = default_temperature
        self.session_id = session_id
        self.logger = logging.getLogger(__name__)
    
    def create_agent(
        self,
        name: str,
        instructions: str,
        is_orchestrator: bool = False,
        team_config: Dict[str, Any] = None,
        agent_config: Dict[str, Any] = None,
        token_callback: Optional[Callable] = None
    ) -> Agent:
        """
        Create a single agent with the given configuration.
        
        Args:
            name: Agent name
            instructions: Agent instructions
            is_orchestrator: Whether this agent is an orchestrator
            team_config: Team configuration for orchestrator context
            agent_config: Agent-specific configuration from YAML
            token_callback: Optional callback function to report token usage
            
        Returns:
            Built OpenAI Agent
            
        Raises:
            ValueError: If required parameters are missing or invalid
        """
        # Validate required parameters
        if not name or not name.strip():
            raise ValueError("Agent name cannot be empty")
        
        if not instructions or not instructions.strip():
            raise ValueError(f"Agent instructions cannot be empty for agent '{name}'")
        
        # Validate tool resolver is available
        if not self.tool_resolver:
            raise ValueError(f"Tool resolver not available for agent '{name}'")
        
        try:
            # Get agent-specific model configuration
            agent_model = self._get_agent_model(agent_config)
            agent_temperature = self._get_agent_temperature(agent_config, agent_model)
            
            # Create system prompt
            system_prompt = self._build_system_prompt(
                name, instructions, is_orchestrator, team_config, agent_config
            )
            
            # Set up provider for the model
            setup_provider_for_model(agent_model)
            
            # Create model settings with reasoning support
            model_settings = self._create_model_settings(agent_config, agent_model, agent_temperature)
            
            # Resolve tools for this agent
            openai_tools = self._resolve_agent_tools(name, agent_config, team_config)
            
            # Get MCP servers for this agent
            agent_mcp_servers = self._get_agent_mcp_servers(agent_config, team_config)
            
            # Create the OpenAI Agent
            agent = Agent(
                name=name,
                instructions=system_prompt,
                model=agent_model,
                model_settings=model_settings,
                tools=openai_tools,
                mcp_servers=agent_mcp_servers,
            )
            
            # Set up agent context
            agent.context = self._build_agent_context(name)
            
            self.logger.info(f"Created agent '{name}' with {len(openai_tools)} tools and {len(agent_mcp_servers)} MCP servers")
            return agent
            
        except Exception as e:
            self.logger.error(f"Failed to create agent '{name}': {e}")
            raise ValueError(f"Agent creation failed for '{name}': {e}") from e
    
    def _has_knowledge_manager(self) -> bool:
        """Check if knowledge manager is available."""
        return (hasattr(self.tool_resolver, 'knowledge_manager') and 
                self.tool_resolver.knowledge_manager is not None)
    
    def _build_agent_context(self, agent_name: str) -> Dict[str, Any]:
        """Build context dictionary for agent."""
        context = {
            "agent_id": agent_name,
            "agent_name": agent_name
        }
        
        # Add knowledge manager if available
        if self._has_knowledge_manager():
            context["knowledge_manager"] = self.tool_resolver.knowledge_manager
        
        # Add session ID if available
        if self.session_id:
            context["session_id"] = self.session_id
        
        return context
    
    def _get_agent_model(self, agent_config: Dict[str, Any]) -> str:
        """Get model for agent, with fallback to default."""
        if agent_config:
            model = agent_config.get('model', self.default_model)
            if not model or not isinstance(model, str):
                return self.default_model
            return model
        return self.default_model
    
    def _get_agent_temperature(self, agent_config: Dict[str, Any], model: str) -> float:
        """Get temperature for agent, with fallback to default. Force temperature=1 for reasoning models."""
        # For reasoning models (gpt-5), temperature must be 1
        if model and 'gpt-5' in model.lower():
            return 1.0
            
        if agent_config:
            temperature = agent_config.get('temperature', self.default_temperature)
            if not isinstance(temperature, (int, float)) or temperature < 0 or temperature > 2:
                self.logger.warning(f"Invalid temperature {temperature}, using default {self.default_temperature}")
                return self.default_temperature
            return float(temperature)
        return self.default_temperature
    
    def _create_model_settings(self, agent_config: Dict[str, Any], model: str, temperature: float) -> ModelSettings:
        """Create ModelSettings with proper reasoning configuration."""
        settings = {"temperature": temperature}
        
        # Only add reasoning for reasoning models (gpt-5)
        if model and 'gpt-5' in model.lower():
            reasoning_effort = agent_config.get('reasoning_effort', 'low') if agent_config else 'low'
            if reasoning_effort in ['minimal', 'low', 'medium', 'high']:
                settings["reasoning_effort"] = reasoning_effort
                self.logger.debug(f"Setting reasoning effort to '{reasoning_effort}' for model '{model}'")
            else:
                self.logger.warning(f"Invalid reasoning_effort '{reasoning_effort}' for model '{model}'. Must be one of: minimal, low, medium, high. Using default 'low'")
                settings["reasoning_effort"] = 'low'
            settings['summary'] = 'auto'

        return ModelSettings(**settings)
    
    def _build_system_prompt(
        self,
        name: str,
        instructions: str,
        is_orchestrator: bool,
        team_config: Dict[str, Any],
        agent_config: Dict[str, Any]
    ) -> str:
        """Build system prompt for agent."""
        knowledge_descriptions = self._get_knowledge_descriptions()
        agent_tools = agent_config.get('tools', []) if agent_config else []
        
        if is_orchestrator:
            prompt_components = build_agent_system_prompt(
                name, instructions, agent_tools, 
                self.tool_resolver.tool_manager, agent_config, knowledge_descriptions, team_config
            )
        else:
            prompt_components = build_agent_system_prompt(
                name, instructions, agent_tools, 
                self.tool_resolver.tool_manager, agent_config, knowledge_descriptions
            )
        
        return self._format_prompt_components(prompt_components)
    
    def _get_knowledge_descriptions(self) -> Dict[str, Any]:
        """Get knowledge descriptions from knowledge registry."""
        if not self._has_knowledge_manager():
            return {}
        
        # Get knowledge registry from knowledge loader if available
        if hasattr(self.tool_resolver, '_knowledge_registry'):
            return self.tool_resolver._knowledge_registry.get_all_descriptions()
        
        return {}
    
    def _format_prompt_components(self, prompt_components: Dict[str, str]) -> str:
        """Format prompt components into final prompt string."""
        background = prompt_components["background"]
        steps = prompt_components["steps"]
        output_instructions = prompt_components["output_instructions"]
        
        return f"{background}\\n\\n{steps}\\n\\n{output_instructions}"
    
    def _resolve_agent_tools(
        self, 
        agent_name: str, 
        agent_config: Dict[str, Any], 
        team_config: Dict[str, Any]
    ) -> List[Any]:
        """Resolve tools for agent."""
        # Get regular tools (non-MCP)
        all_tools = agent_config.get('tools', []) if agent_config else []
        agent_tools = []
        
        for tool_ref in all_tools:
            if not self.mcp_registry.is_mcp_tool(tool_ref, team_config):
                agent_tools.append(tool_ref)
        
        # Knowledge tools are handled automatically by tool_resolver based on agent_config['knowledge']
        # No need to manually add them to agent_tools list
        
        return self.tool_resolver.resolve_tools_for_agent(
            agent_name, agent_tools, agent_config, team_config
        )
    
    def _get_agent_mcp_servers(
        self, 
        agent_config: Dict[str, Any], 
        team_config: Dict[str, Any]
    ) -> List[Any]:
        """Get MCP servers for agent."""
        if not agent_config:
            return []
        
        # Get MCP tool references from agent config
        all_tools = agent_config.get('tools', [])
        mcp_servers_config = agent_config.get('mcp_servers', [])  # Backward compatibility
        
        mcp_tool_references = []
        for tool_ref in all_tools:
            if self.mcp_registry.is_mcp_tool(tool_ref, team_config):
                mcp_tool_references.append(tool_ref)
        
        # Combine MCP tools with backward compatibility mcp_servers
        all_mcp_references = mcp_tool_references + mcp_servers_config
        
        return self.mcp_registry.get_servers_for_agent(all_mcp_references, team_config)
    
    def get_delegate_tools(self) -> Dict[str, Any]:
        """Get delegate tools for team dependency setup."""
        return self.tool_resolver.get_delegate_tools()