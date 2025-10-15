"""
Custom exceptions for team building process.
Provides specific error types for better error handling and debugging.
"""


class TeamBuildingError(Exception):
    """Base exception for team building errors."""
    pass


class ConfigurationError(TeamBuildingError):
    """Raised when there are configuration-related errors."""
    pass


class ComponentInitializationError(TeamBuildingError):
    """Raised when component initialization fails."""
    pass


class AgentCreationError(TeamBuildingError):
    """Raised when agent creation fails."""
    pass


class TeamAssemblyError(TeamBuildingError):
    """Raised when team assembly fails."""
    pass


class KnowledgeLoadingError(TeamBuildingError):
    """Raised when knowledge base loading fails."""
    pass


class ToolRegistrationError(TeamBuildingError):
    """Raised when tool registration fails."""
    pass


class MCPConnectionError(TeamBuildingError):
    """Raised when MCP server connection fails."""
    pass


class ValidationError(TeamBuildingError):
    """Raised when validation fails."""
    pass