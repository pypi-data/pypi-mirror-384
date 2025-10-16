"""MCP server factory for creating different types of MCP servers."""

import logging
from typing import Dict, Any, Optional
from agents.mcp import (
    MCPServerStreamableHttp, MCPServerStreamableHttpParams,
    MCPServerSse, MCPServerSseParams,
    MCPServerStdio, MCPServerStdioParams,
)


class MCPServerFactory:
    """Factory for creating MCP servers based on configuration."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def create_server(self, tool_config: Dict[str, Any]) -> Optional[Any]:
        """
        Create an MCP server based on the tool configuration.
        
        Args:
            tool_config: Tool configuration dictionary
            
        Returns:
            MCP server instance or None if creation fails
        """
        tool_name = tool_config.get('name')
        tool_url = tool_config.get('url')
        tool_command = tool_config.get('command')
        
        if not (tool_url or tool_command):
            return None
        
        connection_type = tool_config.get('connection_type', 'sse').lower()
        
        try:
            if connection_type == 'sse':
                return self._create_sse_server(tool_config, tool_name, tool_url)
            elif connection_type == 'streamable_http':
                return self._create_streamable_http_server(tool_config, tool_name, tool_url)
            elif connection_type == 'stdio':
                return self._create_stdio_server(tool_config, tool_name, tool_command)
            else:
                raise ValueError(f"Unsupported connection_type: {connection_type}")
        
        except Exception as e:
            self.logger.error(f"Failed to create MCP server '{tool_name}': {e}")
            return None
    
    def _create_sse_server(self, tool_config: Dict[str, Any], tool_name: str, tool_url: str) -> MCPServerSse:
        """Create SSE MCP server."""
        params = MCPServerSseParams(
            url=tool_url,
            headers=tool_config.get('headers', {}),
            timeout=tool_config.get('timeout', 30),
            sse_read_timeout=tool_config.get('sse_read_timeout', 30),
        )
        
        server = MCPServerSse(
            params=params,
            name=tool_name,
            cache_tools_list=True,
            client_session_timeout_seconds=tool_config.get('client_session_timeout_seconds', 30),
        )
        
        self.logger.debug(f"Created SSE MCP server '{tool_name}' with params: {params}")
        return server
    
    def _create_streamable_http_server(self, tool_config: Dict[str, Any], tool_name: str, tool_url: str) -> MCPServerStreamableHttp:
        """Create Streamable HTTP MCP server."""
        params = MCPServerStreamableHttpParams(
            url=tool_url,
            headers=tool_config.get('headers', {}),
            timeout=tool_config.get('timeout', 30),
            sse_read_timeout=tool_config.get('sse_read_timeout', 30),
            terminate_on_close=tool_config.get('terminate_on_close', True)
        )
        
        server = MCPServerStreamableHttp(
            params=params,
            name=tool_name,
            client_session_timeout_seconds=tool_config.get('client_session_timeout_seconds', 30),
        )
        
        self.logger.debug(f"Created Streamable HTTP MCP server '{tool_name}' with params: {params}")
        return server
    
    def _create_stdio_server(self, tool_config: Dict[str, Any], tool_name: str, tool_command: str) -> MCPServerStdio:
        """Create Stdio MCP server."""
        params = MCPServerStdioParams(
            command=tool_command,
            args=tool_config.get('args', []),
        )
        
        server = MCPServerStdio(
            params=params,
            name=tool_name,
            client_session_timeout_seconds=tool_config.get('client_session_timeout_seconds', 30),
        )
        
        self.logger.debug(f"Created Stdio MCP server '{tool_name}' with params: {params}")
        return server