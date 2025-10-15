"""
Gnosari Tools - Modular tool system for AI agents.

This package provides a comprehensive tool system with:
- Base classes for creating new tools
- Built-in tools for common operations
- MCP (Model Context Protocol) integration
- Tool registry and discovery system
"""

from .base import BaseTool, SimpleStringTool, ToolRegistry, tool_registry
from .registry import ToolManager, ToolLoader, tool_manager
from .interfaces import AsyncTool, SyncTool

# Import builtin tools for backward compatibility
from .builtin import (
    DelegateAgentTool,
    APIRequestTool, 
    FileOperationsTool,
    KnowledgeQueryTool,
    BashOperationsTool,
    InteractiveBashOperationsTool,
    MySQLQueryTool,
    WebsiteContentTool
    # AWSDiscoveryTool  # Commented out due to missing boto3 dependency
)

# Legacy compatibility imports - removed set_team_dependencies (no longer needed with TeamContext)

__all__ = [
    # Base classes
    "BaseTool",
    "SimpleStringTool", 
    "ToolRegistry",
    "ToolManager",
    "ToolLoader",
    
    # Interfaces
    "AsyncTool",
    "SyncTool",
    
    # Global instances
    "tool_registry",
    "tool_manager",
    
    # Built-in tools
    "DelegateAgentTool",
    "APIRequestTool",
    "FileOperationsTool", 
    "KnowledgeQueryTool",
    "BashOperationsTool",
    "InteractiveBashOperationsTool",
    "MySQLQueryTool",
    "WebsiteContentTool",
    # "AWSDiscoveryTool",  # Commented out due to missing boto3 dependency
    
    # Legacy compatibility - removed set_team_dependencies
]