"""Configuration validation functionality."""

import logging
from typing import Dict, Any, List


class ConfigValidator:
    """Validates team configuration structure and content."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def validate_team_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate team configuration structure.
        
        Args:
            config: Team configuration dictionary
            
        Returns:
            True if valid, raises ValueError if invalid
        """
        if 'agents' not in config:
            raise ValueError("Team configuration must contain 'agents' section")
        
        agents = config['agents']
        if not isinstance(agents, list) or len(agents) == 0:
            raise ValueError("Team configuration must have at least one agent")
        
        # Validate each agent
        for i, agent in enumerate(agents):
            self._validate_agent_config(agent, i)
        
        # Validate handoff references
        self._validate_handoff_references(config)
        
        # Validate no duplicates
        self._validate_no_duplicates(config)
        
        return True
    
    def _validate_agent_config(self, agent: Dict[str, Any], index: int) -> None:
        """Validate individual agent configuration."""
        if 'name' not in agent:
            raise ValueError(f"Agent at index {index} must have a 'name' field")
        
        if 'instructions' not in agent:
            raise ValueError(f"Agent '{agent.get('name', f'at index {index}')}' must have 'instructions' field")
        
        # Validate tools if present
        if 'tools' in agent and not isinstance(agent['tools'], list):
            raise ValueError(f"Agent '{agent['name']}' tools must be a list")
        
        # Validate knowledge if present
        if 'knowledge' in agent and not isinstance(agent['knowledge'], list):
            raise ValueError(f"Agent '{agent['name']}' knowledge must be a list")
    
    def _validate_handoff_references(self, config: Dict[str, Any]) -> None:
        """Validate that handoff references point to existing agents."""
        agent_names = {agent['name'] for agent in config['agents']}
        
        for agent in config['agents']:
            can_transfer_to = agent.get('can_transfer_to', [])
            for transfer_config in can_transfer_to:
                if isinstance(transfer_config, str):
                    target_name = transfer_config
                elif isinstance(transfer_config, dict):
                    target_name = transfer_config.get('agent')
                else:
                    continue
                
                if target_name and target_name not in agent_names:
                    self.logger.warning(
                        f"Agent '{agent['name']}' references non-existent agent '{target_name}' in can_transfer_to"
                    )
    
    def _validate_no_duplicates(self, config: Dict[str, Any]) -> None:
        """Validate no duplicate agent names/IDs, tool names/IDs, or knowledge base names/IDs."""
        
        # Validate no duplicate agent names or IDs
        agent_names = []
        agent_ids = []
        for agent in config['agents']:
            name = agent.get('name')
            agent_id = agent.get('id')
            
            if name:
                if name in agent_names:
                    raise ValueError(f"Duplicate agent name: '{name}'")
                agent_names.append(name)
            
            if agent_id:
                if agent_id in agent_ids:
                    raise ValueError(f"Duplicate agent ID: '{agent_id}'")
                agent_ids.append(agent_id)
        
        # Validate no duplicate tool names or IDs
        if 'tools' in config:
            tool_names = []
            tool_ids = []
            for tool in config['tools']:
                name = tool.get('name')
                tool_id = tool.get('id')
                
                if name:
                    if name in tool_names:
                        raise ValueError(f"Duplicate tool name: '{name}'")
                    tool_names.append(name)
                
                if tool_id:
                    if tool_id in tool_ids:
                        raise ValueError(f"Duplicate tool ID: '{tool_id}'")
                    tool_ids.append(tool_id)
        
        # Validate no duplicate knowledge base names or IDs
        if 'knowledge' in config:
            knowledge_names = []
            knowledge_ids = []
            for kb in config['knowledge']:
                name = kb.get('name')
                kb_id = kb.get('id')
                
                if name:
                    if name in knowledge_names:
                        raise ValueError(f"Duplicate knowledge base name: '{name}'")
                    knowledge_names.append(name)
                
                if kb_id:
                    if kb_id in knowledge_ids:
                        raise ValueError(f"Duplicate knowledge base ID: '{kb_id}'")
                    knowledge_ids.append(kb_id)
        
        # Validate no duplicate MCP server references across tools and agent mcp_servers
        mcp_servers = []
        
        # Check tools for MCP server configs
        if 'tools' in config:
            for tool in config['tools']:
                if 'url' in tool:  # MCP server tool
                    server_ref = tool.get('name', tool.get('url'))
                    if server_ref in mcp_servers:
                        raise ValueError(f"Duplicate MCP server reference: '{server_ref}'")
                    mcp_servers.append(server_ref)
        
        # Check agents for mcp_servers field
        for agent in config['agents']:
            agent_mcp_servers = agent.get('mcp_servers', [])
            for server_name in agent_mcp_servers:
                if server_name in mcp_servers:
                    raise ValueError(f"Duplicate MCP server reference: '{server_name}' (found in both tools and agent mcp_servers)")
                mcp_servers.append(server_name)