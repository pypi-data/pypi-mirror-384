"""
Team Factory - Handles team creation and assembly following SRP.
"""

import logging
from typing import Dict, List, Optional, Any, Callable

from ...core.team import Team
from ..config.team_configuration_manager import TeamConfig
from ..agents import AgentFactory, HandoffConfigurator
from ...traits import TraitManagerInterface
from ...schemas.trait import TraitConfig


class TeamFactory:
    """
    Factory for creating and assembling Team objects.
    Follows Single Responsibility Principle by focusing only on team creation.
    """
    
    def __init__(self, agent_factory: AgentFactory, handoff_configurator: HandoffConfigurator, trait_manager: TraitManagerInterface = None):
        """
        Initialize team factory with required dependencies.
        
        Args:
            agent_factory: Factory for creating individual agents
            handoff_configurator: Configurator for agent handoffs
            trait_manager: Manager for processing agent traits
        """
        self.agent_factory = agent_factory
        self.handoff_configurator = handoff_configurator
        self.trait_manager = trait_manager
        self.logger = logging.getLogger(__name__)
    
    async def create_team(
        self,
        config: TeamConfig,
        token_callback: Optional[Callable] = None
    ) -> Team:
        """
        Create a complete team from configuration.
        
        Args:
            config: Validated team configuration
            token_callback: Optional callback for token usage reporting
            
        Returns:
            Team: Assembled team with orchestrator and workers
            
        Raises:
            ValueError: If team cannot be created from configuration
        """
        try:
            # Build all agents
            all_agents = await self._build_all_agents(config, token_callback)
            
            # Configure handoffs between agents  
            self.handoff_configurator.configure_handoffs(all_agents)
            
            # Assemble team
            team = self._assemble_team(config, all_agents)
            
            self.logger.info(f"Successfully created team '{team.name}' with {len(team.all_agents)} agents")
            return team
            
        except Exception as e:
            self.logger.error(f"Failed to create team: {e}")
            raise ValueError(f"Team creation failed: {e}") from e
    
    async def _build_all_agents(
        self,
        config: TeamConfig,
        token_callback: Optional[Callable]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Build all agents from configuration.
        
        Args:
            config: Team configuration
            token_callback: Optional token usage callback
            
        Returns:
            Dict mapping agent names to agent info dictionaries
        """
        all_agents = {}
        agent_id_to_name = {}
        
        for agent_config in config.agents:
            agent_info = await self._build_single_agent(
                agent_config, 
                config.raw_config, 
                token_callback
            )
            
            name = agent_config['name']
            agent_id = agent_config.get('id')
            
            all_agents[name] = agent_info
            
            # Store ID-to-name mapping if ID is present
            if agent_id:
                agent_id_to_name[agent_id] = name
                self.logger.debug(f"Mapped agent ID '{agent_id}' to name '{name}'")
        
        # Store for team creation
        self.agent_id_to_name = agent_id_to_name
        return all_agents
    
    async def _build_single_agent(
        self,
        agent_config: Dict[str, Any],
        team_config: Dict[str, Any],
        token_callback: Optional[Callable]
    ) -> Dict[str, Any]:
        """
        Build a single agent from configuration.
        
        Args:
            agent_config: Individual agent configuration
            team_config: Full team configuration for context
            token_callback: Optional token usage callback
            
        Returns:
            Dict containing agent instance and metadata
        """
        name = agent_config['name']
        instructions = agent_config['instructions']
        is_orchestrator = agent_config.get('orchestrator', False)
        
        self.logger.debug(f"Building agent '{name}'")
        
        # Process traits if present and trait manager is available
        processed_agent_config = await self._process_agent_traits(name, agent_config)
        
        # Create the agent using the factory
        agent = self.agent_factory.create_agent(
            name=name,
            instructions=instructions,
            is_orchestrator=is_orchestrator,
            team_config=team_config,
            agent_config=processed_agent_config,
            token_callback=token_callback
        )
        
        return {
            'agent': agent,
            'config': processed_agent_config,
            'is_orchestrator': is_orchestrator
        }
    
    async def _process_agent_traits(self, agent_name: str, agent_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process and validate traits for an agent.
        
        Args:
            agent_name: Name of the agent
            agent_config: Agent configuration dictionary
            
        Returns:
            Enhanced agent configuration with processed traits
        """
        # Copy agent config to avoid modifying original
        processed_config = agent_config.copy()
        
        if 'traits' not in agent_config or not agent_config['traits']:
            return processed_config
        
        if not self.trait_manager:
            self.logger.warning(f"Traits defined for agent '{agent_name}' but no trait manager available")
            return processed_config
        
        try:
            # Convert trait dictionaries to TraitConfig objects
            trait_configs = []
            for trait_dict in agent_config['traits']:
                if isinstance(trait_dict, dict):
                    trait_config = TraitConfig(**trait_dict)
                    trait_configs.append(trait_config)
                else:
                    self.logger.warning(f"Invalid trait format for agent '{agent_name}': {trait_dict}")
            
            # Process traits through trait manager
            if trait_configs:
                trait_result = await self.trait_manager.process_traits_for_agent(
                    agent_name, trait_configs
                )
                
                # Add processed traits back to config (as dicts for prompt builder)
                processed_config['traits'] = [trait.dict() for trait in trait_result['traits']]
                
                # Log trait processing results
                if trait_result.get('validation_warnings'):
                    for warning in trait_result['validation_warnings']:
                        self.logger.warning(f"Trait warning for agent '{agent_name}': {warning}")
                
                self.logger.info(f"Successfully processed {len(trait_configs)} traits for agent '{agent_name}'")
            
        except Exception as e:
            self.logger.error(f"Failed to process traits for agent '{agent_name}': {e}")
            # Continue without traits rather than failing
            processed_config.pop('traits', None)
        
        return processed_config
    
    def _assemble_team(
        self,
        config: TeamConfig,
        all_agents: Dict[str, Dict[str, Any]]
    ) -> Team:
        """
        Assemble team object from agents.
        
        Args:
            config: Team configuration
            all_agents: Dictionary of all built agents
            
        Returns:
            Team: Assembled team object
            
        Raises:
            ValueError: If no valid orchestrator can be determined
        """
        orchestrator = None
        workers = {}
        
        # Separate orchestrator from workers
        for name, agent_info in all_agents.items():
            if agent_info['is_orchestrator']:
                orchestrator = agent_info['agent']
            else:
                workers[name] = agent_info['agent']
        
        # Use first agent as orchestrator if none specified
        if orchestrator is None and workers:
            first_agent_name = list(workers.keys())[0]
            orchestrator = workers.pop(first_agent_name)
            self.logger.warning(f"No orchestrator found, using '{first_agent_name}' as orchestrator")
        
        if orchestrator is None:
            raise ValueError("No agents found in team configuration")
        
        # Create team
        max_turns = config.config.get('max_turns') if config.config else None
        team = Team(
            orchestrator=orchestrator,
            workers=workers,
            name=config.name,
            max_turns=max_turns,
            agent_id_to_name=getattr(self, 'agent_id_to_name', {}),
            original_config=config.raw_config
        )
        
        return team