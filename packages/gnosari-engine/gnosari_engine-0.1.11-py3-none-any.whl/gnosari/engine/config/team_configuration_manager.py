"""
Team Configuration Manager - Handles all team configuration concerns following SRP.
"""

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path

from .config_loader import ConfigLoader
from .validator import ConfigValidator
from .env_substitutor import EnvironmentVariableSubstitutor
from ..exceptions import ConfigurationError, ValidationError


@dataclass
class TeamConfig:
    """Validated team configuration data class."""
    name: Optional[str]
    description: Optional[str]
    agents: list[Dict[str, Any]]
    tools: Optional[list[Dict[str, Any]]] = None
    knowledge: Optional[list[Dict[str, Any]]] = None
    config: Optional[Dict[str, Any]] = None
    queues: Optional[list[Dict[str, Any]]] = None
    events: Optional[Dict[str, Any]] = None
    raw_config: Optional[Dict[str, Any]] = None


class TeamConfigurationManager:
    """
    Manages team configuration loading, validation, and processing.
    Follows Single Responsibility Principle by focusing only on configuration concerns.
    """
    
    def __init__(
        self,
        config_loader: Optional[ConfigLoader] = None,
        config_validator: Optional[ConfigValidator] = None,
        env_substitutor: Optional[EnvironmentVariableSubstitutor] = None
    ):
        """
        Initialize configuration manager with optional dependencies.
        
        Args:
            config_loader: Configuration loader instance
            config_validator: Configuration validator instance  
            env_substitutor: Environment variable substitutor instance
        """
        self.logger = logging.getLogger(__name__)
        
        # Use dependency injection with sensible defaults
        self.env_substitutor = env_substitutor or EnvironmentVariableSubstitutor()
        self.config_validator = config_validator or ConfigValidator()
        self.config_loader = config_loader or ConfigLoader(
            self.env_substitutor, 
            self.config_validator
        )
    
    def load_team_config(self, config_path: str) -> TeamConfig:
        """
        Load and validate team configuration from file.
        
        Args:
            config_path: Path to the YAML configuration file
            
        Returns:
            TeamConfig: Validated configuration object
            
        Raises:
            ConfigurationError: If config file doesn't exist or is invalid
            ValidationError: If configuration validation fails
        """
        try:
            # Validate file exists
            config_file = Path(config_path)
            if not config_file.exists():
                raise ConfigurationError(f"Configuration file not found: {config_path}")
            
            if not config_file.is_file():
                raise ConfigurationError(f"Configuration path is not a file: {config_path}")
            
            # Load raw configuration
            raw_config = self.config_loader.load_team_config(config_path)
            self.logger.debug(f"Loaded configuration from {config_path}")
            
            # Validate required fields
            self._validate_required_fields(raw_config)
            
            # Create structured config object
            team_config = self._create_team_config(raw_config)
            
            self.logger.info(f"Successfully loaded team '{team_config.name}' with {len(team_config.agents)} agents")
            return team_config
            
        except (ConfigurationError, ValidationError):
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            self.logger.error(f"Failed to load team configuration from {config_path}: {e}")
            raise ConfigurationError(f"Failed to load team configuration from {config_path}: {e}") from e
    
    def _validate_required_fields(self, config: Dict[str, Any]) -> None:
        """
        Validate that required configuration fields are present.
        
        Args:
            config: Raw configuration dictionary
            
        Raises:
            ValidationError: If required fields are missing or invalid
        """
        if not isinstance(config, dict):
            raise ValidationError("Configuration must be a dictionary")
            
        if 'agents' not in config or not config['agents']:
            raise ValidationError("Team configuration must include at least one agent")
        
        if not isinstance(config['agents'], list):
            raise ValidationError("'agents' field must be a list")
        
        # Validate each agent
        for i, agent in enumerate(config['agents']):
            if not isinstance(agent, dict):
                raise ValidationError(f"Agent at index {i} must be a dictionary")
                
            if 'name' not in agent or not agent['name']:
                raise ValidationError(f"Agent at index {i} is missing required 'name' field")
                
            if not isinstance(agent['name'], str):
                raise ValidationError(f"Agent at index {i}: 'name' field must be a string")
                
            if 'instructions' not in agent or not agent['instructions']:
                raise ValidationError(f"Agent '{agent['name']}' is missing required 'instructions' field")
                
            if not isinstance(agent['instructions'], str):
                raise ValidationError(f"Agent '{agent['name']}': 'instructions' field must be a string")
        
        # Validate tools if present
        if 'tools' in config and config['tools'] is not None:
            if not isinstance(config['tools'], list):
                raise ValidationError("'tools' field must be a list")
        
        # Validate knowledge if present
        if 'knowledge' in config and config['knowledge'] is not None:
            if not isinstance(config['knowledge'], list):
                raise ValidationError("'knowledge' field must be a list")
        
        # Validate queues if present
        if 'queues' in config and config['queues'] is not None:
            if not isinstance(config['queues'], list):
                raise ValidationError("'queues' field must be a list")
        
        # Validate events if present
        if 'events' in config and config['events'] is not None:
            if not isinstance(config['events'], dict):
                raise ValidationError("'events' field must be a dictionary")
    
    def _create_team_config(self, raw_config: Dict[str, Any]) -> TeamConfig:
        """
        Create structured TeamConfig from raw configuration.
        
        Args:
            raw_config: Raw configuration dictionary
            
        Returns:
            TeamConfig: Structured configuration object
        """
        return TeamConfig(
            name=raw_config.get('name'),
            description=raw_config.get('description'),
            agents=raw_config['agents'],
            tools=raw_config.get('tools'),
            knowledge=raw_config.get('knowledge'),
            config=raw_config.get('config'),
            queues=raw_config.get('queues'),
            events=raw_config.get('events'),
            raw_config=raw_config
        )
    
    def has_knowledge_bases(self, config: TeamConfig) -> bool:
        """Check if configuration includes knowledge bases."""
        return config.knowledge is not None and len(config.knowledge) > 0
    
    def has_tools(self, config: TeamConfig) -> bool:
        """Check if configuration includes tools."""
        return config.tools is not None and len(config.tools) > 0
    
    def get_orchestrator_agents(self, config: TeamConfig) -> list[Dict[str, Any]]:
        """Get all agents marked as orchestrators."""
        return [agent for agent in config.agents if agent.get('orchestrator', False)]
    
    def get_worker_agents(self, config: TeamConfig) -> list[Dict[str, Any]]:
        """Get all agents that are not orchestrators."""
        return [agent for agent in config.agents if not agent.get('orchestrator', False)]
    
    def get_max_turns(self, config: TeamConfig) -> Optional[int]:
        """Get maximum turns configuration."""
        return config.config.get('max_turns') if config.config else None
    
    def has_queues(self, config: TeamConfig) -> bool:
        """Check if configuration includes queue definitions."""
        return config.queues is not None and len(config.queues) > 0
    
    def has_events(self, config: TeamConfig) -> bool:
        """Check if configuration includes event settings."""
        return config.events is not None
    
    def get_event_listeners(self, config: TeamConfig) -> list[Dict[str, Any]]:
        """Get all agents with event listener configurations."""
        listeners = []
        for agent in config.agents:
            if 'listen' in agent and agent['listen']:
                listeners.append({
                    'agent': agent,
                    'listener_config': agent['listen']
                })
        return listeners
    
    def get_event_triggers(self, config: TeamConfig) -> list[Dict[str, Any]]:
        """Get all agents with event trigger configurations."""
        triggers = []
        for agent in config.agents:
            if 'trigger' in agent and agent['trigger']:
                for trigger in agent['trigger']:
                    triggers.append({
                        'agent': agent,
                        'trigger_config': trigger
                    })
        return triggers