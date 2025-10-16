"""
Core package for Gnosari AI Teams.

This package contains fundamental classes and interfaces for the Gnosari framework.
"""

from .team import Team
from .agent import BaseAgent, GnosariAgent, AgentConfig
from .config import TeamConfig, KnowledgeConfig, ToolConfig
from .exceptions import (
    GnosariError, 
    ConfigurationError, 
    AgentError, 
    ToolError, 
    KnowledgeError, 
    ProviderError
)

__all__ = [
    'Team',
    'BaseAgent', 
    'GnosariAgent',
    'AgentConfig',
    'TeamConfig',
    'KnowledgeConfig', 
    'ToolConfig',
    'GnosariError', 
    'ConfigurationError', 
    'AgentError',
    'ToolError',
    'KnowledgeError',
    'ProviderError'
]