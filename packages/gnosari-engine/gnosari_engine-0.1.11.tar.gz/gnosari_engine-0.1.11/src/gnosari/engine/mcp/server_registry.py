"""MCP server registry for managing server references and mappings."""

import logging
from typing import Dict, List, Any


class MCPServerRegistry:
    """Registry for managing MCP server references and mappings."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.server_id_to_name: Dict[str, str] = {}
        self.servers: List[Any] = []
    
    def register_servers(self, servers: List[Any], tools_config: List[Dict[str, Any]]):
        """
        Register MCP servers and their ID-to-name mappings.
        
        Args:
            servers: List of MCP server instances
            tools_config: List of tool configurations
        """
        self.servers = servers
        self._build_id_to_name_mapping(tools_config)
    
    def _build_id_to_name_mapping(self, tools_config: List[Dict[str, Any]]):
        """Build mapping from server IDs to names."""
        for tool_config in tools_config:
            tool_name = tool_config.get('name')
            tool_id = tool_config.get('id')
            tool_url = tool_config.get('url')
            tool_command = tool_config.get('command')
            
            # Only process MCP server configurations
            if (tool_url or tool_command) and tool_id and tool_name:
                self.server_id_to_name[tool_id] = tool_name
                self.logger.debug(f"Mapped MCP server ID '{tool_id}' to name '{tool_name}'")
    
    def is_mcp_tool(self, tool_ref: str, config: Dict[str, Any]) -> bool:
        """
        Check if a tool reference corresponds to an MCP server.
        
        Args:
            tool_ref: Tool reference (name or ID)
            config: Team configuration
            
        Returns:
            True if this tool reference is an MCP server, False otherwise
        """
        if 'tools' not in config:
            return False
        
        # First resolve ID to name if needed
        tool_name = self.resolve_tool_reference(tool_ref)
        
        # Check if any tool configuration has this name and is an MCP server
        for tool_config in config['tools']:
            config_name = tool_config.get('name')
            tool_url = tool_config.get('url')
            tool_command = tool_config.get('command')
            
            if config_name == tool_name and (tool_url or tool_command):
                return True
        
        return False
    
    def resolve_tool_reference(self, tool_ref: str) -> str:
        """
        Resolve tool reference (ID or name) to name.
        
        Args:
            tool_ref: Tool reference (name or ID)
            
        Returns:
            Tool name
        """
        return self.server_id_to_name.get(tool_ref, tool_ref)
    
    def get_servers_for_agent(self, mcp_server_references: List[str], config: Dict[str, Any]) -> List[Any]:
        """
        Get MCP server instances for an agent based on references.
        
        Args:
            mcp_server_references: List of MCP server names or IDs
            config: Team configuration
            
        Returns:
            List of MCP server instances
        """
        if not mcp_server_references or not self.servers:
            return []
        
        # Get server names this agent should have access to
        server_names = self._get_server_names(mcp_server_references, config)
        
        # Filter actual server instances based on names
        agent_servers = [server for server in self.servers if server.name in server_names]
        
        if server_names:
            self.logger.debug(f"Agent gets MCP servers: {[server.name for server in agent_servers]}")
        
        return agent_servers
    
    def _get_server_names(self, mcp_server_references: List[str], config: Dict[str, Any]) -> List[str]:
        """
        Get the names of MCP servers that should be included for an agent.
        
        Args:
            mcp_server_references: List of MCP server names or IDs to include
            config: Team configuration
            
        Returns:
            List of MCP server names that exist in the configuration
        """
        if 'tools' not in config:
            return []
        
        # First resolve any IDs to names
        resolved_server_names = []
        for server_ref in mcp_server_references:
            resolved_name = self.resolve_tool_reference(server_ref)
            resolved_server_names.append(resolved_name)
            if server_ref != resolved_name:
                self.logger.debug(f"Resolved MCP server reference '{server_ref}' to name '{resolved_name}'")
        
        # Check which servers are available in configuration
        available_servers = []
        for tool_config in config['tools']:
            tool_name = tool_config.get('name')
            tool_url = tool_config.get('url')
            tool_command = tool_config.get('command')
            
            if (tool_url or tool_command) and tool_name in resolved_server_names:
                available_servers.append(tool_name)
        
        return available_servers