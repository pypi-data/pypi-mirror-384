"""
Custom exceptions for Gnosari AI Teams.
"""


class GnosariError(Exception):
    """Base exception for all Gnosari errors."""
    pass


class ConfigurationError(GnosariError):
    """Raised when there are configuration issues."""
    pass


class AgentError(GnosariError):
    """Raised when there are agent-related errors."""
    pass


class ToolError(GnosariError):
    """Raised when there are tool-related errors."""
    pass


class KnowledgeError(GnosariError):
    """Raised when there are knowledge base errors."""
    pass


class ProviderError(GnosariError):
    """Raised when there are LLM provider errors."""
    pass