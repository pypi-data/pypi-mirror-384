"""
Component Factory - Creates and configures team building components following DIP.
"""

from abc import ABC, abstractmethod
from typing import Optional, Callable
import logging

from ...tools import ToolManager, KnowledgeQueryTool
from ..mcp import MCPServerFactory, MCPConnectionManager, MCPServerRegistry
from ..knowledge import KnowledgeLoader, KnowledgeRegistry
from ..agents import AgentFactory, ToolResolver, HandoffConfigurator
from ...traits import TraitManager, TraitManagerInterface


class ComponentFactory(ABC):
    """
    Abstract factory for creating team building components.
    Follows Dependency Inversion Principle by depending on abstractions.
    """
    
    @abstractmethod
    def create_mcp_components(self) -> tuple[MCPServerFactory, MCPConnectionManager, MCPServerRegistry]:
        """Create MCP-related components."""
        pass
    
    @abstractmethod
    def create_knowledge_components(self, progress_callback: Optional[Callable] = None) -> tuple[KnowledgeRegistry, KnowledgeLoader]:
        """Create knowledge management components."""
        pass
    
    @abstractmethod
    def create_tool_manager(self) -> ToolManager:
        """Create tool manager."""
        pass
    
    @abstractmethod
    def create_trait_manager(self) -> TraitManagerInterface:
        """Create trait manager."""
        pass
    
    @abstractmethod
    def create_agent_components(
        self,
        tool_manager: ToolManager,
        knowledge_manager,
        mcp_registry: MCPServerRegistry,
        trait_manager: TraitManagerInterface,
        model: str,
        temperature: float,
        session_id: Optional[str]
    ) -> tuple[ToolResolver, AgentFactory, HandoffConfigurator]:
        """Create agent-related components."""
        pass


class DefaultComponentFactory(ComponentFactory):
    """
    Default implementation of ComponentFactory.
    Creates concrete instances of all required components.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def create_mcp_components(self) -> tuple[MCPServerFactory, MCPConnectionManager, MCPServerRegistry]:
        """Create MCP-related components."""
        server_factory = MCPServerFactory()
        connection_manager = MCPConnectionManager(server_factory)
        mcp_registry = MCPServerRegistry()
        
        self.logger.debug("Created MCP components")
        return server_factory, connection_manager, mcp_registry
    
    def create_knowledge_components(self, progress_callback: Optional[Callable] = None) -> tuple[KnowledgeRegistry, KnowledgeLoader]:
        """Create knowledge management components."""
        knowledge_registry = KnowledgeRegistry()
        knowledge_loader = KnowledgeLoader(knowledge_registry, progress_callback)
        
        self.logger.debug("Created knowledge components")
        return knowledge_registry, knowledge_loader
    
    def create_tool_manager(self) -> ToolManager:
        """Create tool manager."""
        tool_manager = ToolManager()
        self.logger.debug("Created tool manager")
        return tool_manager
    
    def create_trait_manager(self) -> TraitManagerInterface:
        """Create trait manager."""
        trait_manager = TraitManager()
        self.logger.debug("Created trait manager")
        return trait_manager
    
    def create_agent_components(
        self,
        tool_manager: ToolManager,
        knowledge_manager,
        mcp_registry: MCPServerRegistry,
        trait_manager: TraitManagerInterface,
        model: str,
        temperature: float,
        session_id: Optional[str]
    ) -> tuple[ToolResolver, AgentFactory, HandoffConfigurator]:
        """Create agent-related components."""
        tool_resolver = ToolResolver(tool_manager, knowledge_manager, session_id)
        agent_factory = AgentFactory(tool_resolver, mcp_registry, model, temperature, session_id)
        handoff_configurator = HandoffConfigurator()
        
        self.logger.debug("Created agent components")
        return tool_resolver, agent_factory, handoff_configurator


class ComponentRegistry:
    """
    Registry for managing component instances and their lifecycles.
    Implements a simple dependency injection container.
    """
    
    def __init__(self, factory: ComponentFactory):
        self.factory = factory
        self.logger = logging.getLogger(__name__)
        self._instances = {}
    
    def get_or_create_mcp_components(self):
        """Get or create MCP components (singleton pattern)."""
        if 'mcp_components' not in self._instances:
            self._instances['mcp_components'] = self.factory.create_mcp_components()
            self.logger.debug("Registered MCP components in registry")
        return self._instances['mcp_components']
    
    def get_or_create_knowledge_components(self, progress_callback: Optional[Callable] = None):
        """Get or create knowledge components (singleton pattern)."""
        if 'knowledge_components' not in self._instances:
            self._instances['knowledge_components'] = self.factory.create_knowledge_components(progress_callback)
            self.logger.debug("Registered knowledge components in registry")
        return self._instances['knowledge_components']
    
    def get_or_create_tool_manager(self):
        """Get or create tool manager (singleton pattern)."""
        if 'tool_manager' not in self._instances:
            self._instances['tool_manager'] = self.factory.create_tool_manager()
            self.logger.debug("Registered tool manager in registry")
        return self._instances['tool_manager']
    
    def get_or_create_trait_manager(self):
        """Get or create trait manager (singleton pattern)."""
        if 'trait_manager' not in self._instances:
            self._instances['trait_manager'] = self.factory.create_trait_manager()
            self.logger.debug("Registered trait manager in registry")
        return self._instances['trait_manager']
    
    def get_or_create_agent_components(
        self,
        model: str,
        temperature: float,
        session_id: Optional[str]
    ):
        """Get or create agent components."""
        # Agent components are created fresh each time as they depend on runtime parameters
        tool_manager = self.get_or_create_tool_manager()
        trait_manager = self.get_or_create_trait_manager()
        _, knowledge_loader = self.get_or_create_knowledge_components()
        _, _, mcp_registry = self.get_or_create_mcp_components()
        
        # Ensure knowledge manager is initialized BEFORE creating agent components
        knowledge_loader.ensure_knowledge_manager()
        knowledge_manager = knowledge_loader.knowledge_manager
        
        self.logger.debug(f"Creating agent components with knowledge_manager: {knowledge_manager is not None}")
        
        agent_components = self.factory.create_agent_components(
            tool_manager, knowledge_manager, mcp_registry, trait_manager, model, temperature, session_id
        )
        
        self.logger.debug("Created agent components with runtime parameters")
        return agent_components
    
    def clear(self):
        """Clear all registered instances."""
        self._instances.clear()
        self.logger.debug("Cleared component registry")