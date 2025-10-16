"""
Gnosari AI Teams - Framework for orchestrating multi-agent teams.

This package provides a comprehensive framework for building and managing
teams of AI agents that can collaborate on complex tasks.
"""

# Core components
from .core import Team, TeamConfig, GnosariAgent, BaseAgent
from .engine import TeamBuilder, TeamRunner
from .tools import BaseTool, tool_manager, tool_registry
from .knowledge import KnowledgeManager
from .providers import (
    BaseLLMProvider, provider_registry, setup_provider_for_model, 
    setup_provider_by_name, list_available_models
)
from .schemas import BaseIOSchema
from .utils import setup_logging, get_logger

__version__ = "0.1.0"

__all__ = [
    # Core classes
    "Team",
    "TeamConfig", 
    "GnosariAgent",
    "BaseAgent",
    
    # Engine components
    "TeamBuilder",
    "TeamRunner",
    
    # Tools
    "BaseTool",
    "tool_manager", 
    "tool_registry",
    
    # Knowledge
    "KnowledgeManager",
    
    # Providers
    "BaseLLMProvider",
    "provider_registry",
    "setup_provider_for_model",
    "setup_provider_by_name", 
    "list_available_models",
    
    # Schemas
    "BaseIOSchema",
    
    # Utilities
    "setup_logging",
    "get_logger",
    
    # Metadata
    "__version__"
]
