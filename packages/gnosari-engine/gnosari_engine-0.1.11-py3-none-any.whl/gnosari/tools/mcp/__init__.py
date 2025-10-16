"""
MCP (Model Context Protocol) integration for Gnosari AI Teams.

This package handles MCP server integration and tool adaptation.
"""

from .client import MCPClient
from .adapter import MCPToolAdapter

__all__ = ['MCPClient', 'MCPToolAdapter']