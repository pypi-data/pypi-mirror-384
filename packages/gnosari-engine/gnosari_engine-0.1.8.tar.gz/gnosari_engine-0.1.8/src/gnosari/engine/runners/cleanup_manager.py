"""
Resource cleanup coordination for runners
"""

import logging
from typing import List, Optional
from agents.memory.session import SessionABC
from ..event_handlers import MCPServerManager

logger = logging.getLogger(__name__)


class CleanupManager:
    """Coordinates cleanup of various resources used by runners."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def cleanup_interactive_bash_sessions(self) -> None:
        """Clean up all interactive bash sessions using global registry."""
        try:
            from ...tools.builtin.interactive_bash_operations import cleanup_all_global_interactive_bash_sessions
            await cleanup_all_global_interactive_bash_sessions()
            self.logger.debug("Cleaned up interactive bash sessions")
        except Exception as e:
            self.logger.error(f"Error cleaning up interactive bash sessions: {e}")
    
    async def cleanup_session(self, session: Optional[SessionABC]) -> None:
        """Clean up session resources.
        
        Args:
            session: Session to cleanup
        """
        if session and hasattr(session, 'cleanup'):
            try:
                await session.cleanup()
                self.logger.debug("Cleaned up session")
            except Exception as e:
                self.logger.error(f"Error cleaning up session: {e}")
    
    async def cleanup_mcp_servers(self, mcp_manager: MCPServerManager, agents: List) -> None:
        """Clean up MCP servers.
        
        Args:
            mcp_manager: MCP server manager instance
            agents: List of agents whose servers need cleanup
        """
        try:
            await mcp_manager.cleanup_servers(agents)
            self.logger.debug(f"Cleaned up MCP servers for {len(agents)} agents")
        except Exception as e:
            self.logger.error(f"Error cleaning up MCP servers: {e}")
    
    async def cleanup_all(self, session: Optional[SessionABC] = None, 
                         mcp_manager: Optional[MCPServerManager] = None, 
                         agents: Optional[List] = None) -> None:
        """Perform comprehensive cleanup of all resources.
        
        Args:
            session: Session to cleanup
            mcp_manager: MCP server manager
            agents: Agents whose MCP servers need cleanup
        """
        # Clean up interactive bash sessions first
        await self.cleanup_interactive_bash_sessions()
        
        # Clean up session resources
        if session:
            await self.cleanup_session(session)
        
        # Clean up MCP servers
        if mcp_manager and agents:
            await self.cleanup_mcp_servers(mcp_manager, agents)