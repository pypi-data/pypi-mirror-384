"""MCP connection management functionality."""

import asyncio
import logging
from typing import List, Any, Dict
from agents.mcp import MCPServerStdio

from .server_factory import MCPServerFactory


class MCPConnectionManager:
    """Manages MCP server connections and lifecycle."""
    
    def __init__(self, server_factory: MCPServerFactory = None):
        self.server_factory = server_factory or MCPServerFactory()
        self.logger = logging.getLogger(__name__)
        self.failed_connections = []
    
    async def create_and_connect_servers(self, tools_config: List[Dict[str, Any]]) -> List[Any]:
        """
        Create and connect to MCP servers from tool configurations.
        
        Args:
            tools_config: List of tool configurations
            
        Returns:
            List of successfully connected MCP servers
        """
        servers = []
        self.failed_connections = []
        
        for tool_config in tools_config:
            server = await self._create_and_connect_server(tool_config)
            if server:
                servers.append(server)
        
        return servers
    
    async def _create_and_connect_server(self, tool_config: Dict[str, Any]) -> Any:
        """Create and connect a single MCP server."""
        tool_name = tool_config.get('name')
        tool_url = tool_config.get('url')
        tool_command = tool_config.get('command')
        
        if not (tool_url or tool_command):
            return None
        
        server = self.server_factory.create_server(tool_config)
        if not server:
            return None
        
        # Ensure the server has a name attribute
        if not hasattr(server, 'name') or server.name is None:
            server.name = tool_name
        
        # Test connection before adding to agents (skip for stdio servers)
        if isinstance(server, MCPServerStdio):
            # Skip auto-connection for stdio servers - they'll connect when needed
            self.logger.info(f"✅ Created MCP stdio server for '{tool_name}' (connection deferred)")
            return server
        
        # Try to connect for non-stdio servers
        return await self._test_connection(server, tool_config)
    
    async def _test_connection(self, server: Any, tool_config: Dict[str, Any]) -> Any:
        """Test connection to an MCP server."""
        tool_name = tool_config.get('name')
        tool_url = tool_config.get('url')
        tool_command = tool_config.get('command')
        
        try:
            await asyncio.wait_for(server.connect(), timeout=10.0)
            self.logger.info(f"✅ Created and connected MCP server for '{tool_name}'")
            return server
            
        except asyncio.TimeoutError:
            error_msg = "Connection timeout"
            self.logger.warning(f"⚠️  {error_msg} for MCP server '{tool_name}'")
            self._record_failed_connection(tool_name, tool_url or tool_command, error_msg)
            await self._safe_cleanup_server(server, tool_name)
            return None
            
        except asyncio.CancelledError:
            error_msg = "Connection cancelled"
            self.logger.warning(f"⚠️  {error_msg} for MCP server '{tool_name}'")
            self._record_failed_connection(tool_name, tool_url or tool_command, error_msg)
            await self._safe_cleanup_server(server, tool_name)
            return None
            
        except Exception as e:
            error_msg = self._get_error_message(e, tool_name)
            self.logger.warning(f"⚠️  {error_msg}")
            self._record_failed_connection(tool_name, tool_url or tool_command, error_msg.replace(f" for MCP server '{tool_name}'", ""))
            await self._safe_cleanup_server(server, tool_name)
            return None
    
    def _get_error_message(self, error: Exception, tool_name: str) -> str:
        """Get appropriate error message for connection failure."""
        error_str = str(error)
        
        if 'HTTPStatusError' in str(type(error)) or '502 Bad Gateway' in error_str or '404 Not Found' in error_str:
            if '502' in error_str:
                return f"Server unavailable (502 Bad Gateway) for MCP server '{tool_name}'"
            elif '404' in error_str:
                return f"Server not found (404) for MCP server '{tool_name}'"
            else:
                return f"HTTP error for MCP server '{tool_name}': {error}"
        elif 'Session terminated' in error_str:
            return f"Session terminated for MCP server '{tool_name}'"
        else:
            return f"Failed to connect to MCP server '{tool_name}': {error}"
    
    def _record_failed_connection(self, name: str, url: str, error: str):
        """Record a failed connection for reporting."""
        self.failed_connections.append({
            'name': name,
            'url': url,
            'error': error
        })
    
    async def _safe_cleanup_server(self, server: Any, tool_name: str):
        """Safely clean up an MCP server to avoid async generator errors."""
        try:
            # For streamable HTTP servers, we need special handling to avoid async context issues
            if hasattr(server, '_client') and server._client is not None:
                # Manually close the HTTP client session to avoid async context cleanup issues
                try:
                    if hasattr(server._client, 'aclose'):
                        await server._client.aclose()
                    elif hasattr(server._client, 'close'):
                        await server._client.close()
                    self.logger.debug(f"Manually closed HTTP client for MCP server: {tool_name}")
                except Exception as e:
                    self.logger.debug(f"Error manually closing HTTP client for {tool_name}: {e}")
            
            # Now try the normal cleanup
            await asyncio.wait_for(server.cleanup(), timeout=2.0)
            self.logger.debug(f"Successfully cleaned up MCP server: {tool_name}")
        except asyncio.TimeoutError:
            self.logger.debug(f"Cleanup timeout for MCP server: {tool_name}")
        except asyncio.CancelledError:
            self.logger.debug(f"Cleanup cancelled for MCP server: {tool_name}")
        except RuntimeError as e:
            if "cancel scope" in str(e) or "different task" in str(e):
                self.logger.debug(f"Async context error during MCP cleanup for {tool_name} - ignoring")
            else:
                self.logger.warning(f"Runtime error during MCP cleanup for {tool_name}: {e}")
        except Exception as e:
            # Check if this is a known async shutdown error
            if any(phrase in str(e) for phrase in ["cancel scope", "different task", "TaskGroup"]):
                self.logger.debug(f"Async shutdown error during MCP cleanup for {tool_name} - ignoring")
            else:
                self.logger.debug(f"Error during MCP cleanup for {tool_name}: {e}")
    
    async def cleanup_servers(self, servers: List[Any]):
        """Clean up MCP server connections."""
        if servers:
            self.logger.info("Cleaning up MCP server connections...")
            for server in servers:
                try:
                    await self._safe_cleanup_server(server, getattr(server, 'name', 'unknown'))
                except Exception as e:
                    self.logger.debug(f"Error cleaning up MCP server {getattr(server, 'name', 'unknown')}: {e}")
            self.logger.info("MCP server cleanup completed")