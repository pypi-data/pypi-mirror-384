"""
Refactored Team Builder - Uses SOLID principles with specialized components.
Now serves as a simplified facade over the new orchestrated architecture.
"""

import logging
from typing import Optional, Callable

from ..core.team import Team

# Import new SOLID-compliant components
from .config.team_configuration_manager import TeamConfigurationManager
from .factories.component_factory import DefaultComponentFactory, ComponentRegistry
from .orchestrators.team_building_orchestrator import TeamBuildingOrchestrator


class TeamBuilder:
    """
    Simplified team builder that serves as a facade over the new SOLID architecture.
    Maintains backward compatibility while delegating to specialized components.
    """
    
    def __init__(
        self, 
        api_key: Optional[str] = None, 
        model: str = "gpt-4o", 
        temperature: float = 1.0,
        session_id: Optional[str] = None,
        team_identifier: Optional[str] = None,
        progress_callback: Optional[Callable] = None
    ):
        """
        Initialize the team builder with default configuration.
        
        Args:
            api_key: OpenAI API key (optional, will use environment variable if not provided)
            model: Default model to use for agents
            temperature: Default temperature for agents
            session_id: Session ID for context propagation to agents and tools
            team_identifier: Team identifier for session context (extracted from team path)
            progress_callback: Optional callback for progress updates during streaming
        """
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.session_id = session_id
        self.team_identifier = team_identifier
        self.progress_callback = progress_callback
        self.logger = logging.getLogger(__name__)
        
        # Initialize SOLID-compliant architecture
        self._initialize_architecture()
    
    def _initialize_architecture(self):
        """Initialize the new SOLID-compliant architecture."""
        # Create configuration manager
        self.config_manager = TeamConfigurationManager()
        
        # Create component factory and registry
        self.component_factory = DefaultComponentFactory()
        self.component_registry = ComponentRegistry(self.component_factory)
        
        # Create orchestrator
        self.orchestrator = TeamBuildingOrchestrator(
            self.config_manager,
            self.component_registry
        )
        
        self.logger.debug("Initialized SOLID-compliant team building architecture")
    
    def load_team_config(self, config_path: str) -> dict:
        """
        Load team configuration from YAML file.
        
        Args:
            config_path: Path to the YAML configuration file
            
        Returns:
            Team configuration dictionary (for backward compatibility)
        """
        team_config = self.config_manager.load_team_config(config_path)
        return team_config.raw_config
    
    async def build_team(
        self, 
        config_path: str, 
        debug: bool = False, 
        token_callback: Optional[Callable] = None
    ) -> Team:
        """
        Build a complete team from YAML configuration.
        
        Args:
            config_path: Path to the YAML configuration file
            debug: Whether to show debug information
            token_callback: Optional callback function to report token usage
            
        Returns:
            Team object containing orchestrator and worker agents
        """
        return await self.orchestrator.build_team(
            config_path=config_path,
            api_key=self.api_key,
            model=self.model,
            temperature=self.temperature,
            session_id=self.session_id,
            debug=debug,
            token_callback=token_callback
        )
    
    async def build_team_from_modular_path(
        self,
        team_path: str,
        debug: bool = False,
        token_callback: Optional[Callable] = None
    ) -> Team:
        """
        Build a complete team from modular configuration directory.
        Follows Open/Closed Principle by extending functionality without modifying existing code.
        
        Args:
            team_path: Path to the modular team directory
            debug: Whether to show debug information
            token_callback: Optional callback function to report token usage
            
        Returns:
            Team object containing orchestrator and worker agents
        """
        return await self.orchestrator.build_team_from_modular_path(
            team_path=team_path,
            api_key=self.api_key,
            model=self.model,
            temperature=self.temperature,
            session_id=self.session_id,
            debug=debug,
            token_callback=token_callback
        )
    
    async def build_team_smart(
        self,
        config_path: str,
        debug: bool = False,
        token_callback: Optional[Callable] = None
    ) -> Team:
        """
        Smart team builder that auto-detects configuration format.
        Follows Open/Closed Principle by providing unified interface for both formats.
        
        Args:
            config_path: Path to team configuration (file or directory)
            debug: Whether to show debug information
            token_callback: Optional callback function to report token usage
            
        Returns:
            Team object containing orchestrator and worker agents
            
        Raises:
            ValueError: If path doesn't exist or format is invalid
        """
        from pathlib import Path
        
        path = Path(config_path)
        
        if not path.exists():
            raise ValueError(f"Configuration path does not exist: {config_path}")
        
        if path.is_file():
            # Single file configuration - use legacy builder
            self.logger.debug(f"Detected single file configuration: {config_path}")
            return await self.build_team(
                config_path=config_path,
                debug=debug,
                token_callback=token_callback
            )
        elif path.is_dir():
            # Directory configuration - use modular builder
            self.logger.debug(f"Detected modular directory configuration: {config_path}")
            return await self.build_team_from_modular_path(
                team_path=config_path,
                debug=debug,
                token_callback=token_callback
            )
        else:
            raise ValueError(f"Invalid configuration path (not file or directory): {config_path}")
    
    async def cleanup_mcp_servers(self):
        """
        Clean up MCP server connections.
        Delegates to the orchestrator for proper cleanup.
        """
        await self.orchestrator.cleanup()