"""
Modular configuration manager for Gnosari AI Teams.

This module manages loading, validation, and composition of modular team configurations
with hierarchical overrides and component dependency resolution.
"""
import yaml
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from copy import deepcopy
import logging

from .inferred_component_loader import InferredComponentLoader, ComponentValidationError
from ...schemas.modular_config import (
    TeamMainConfig, ModularTeamConfig, AgentComponentConfig, 
    ToolComponentConfig, KnowledgeComponentConfig, PromptComponentConfig, TraitComponentConfig
)
from ...schemas.team import TeamCreateRequest

logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Raised when configuration loading or validation fails."""
    pass


class ConfigurationManager:
    """Manages loading and composition of modular team configurations."""
    
    def __init__(self, base_path: Optional[Path] = None):
        self.base_path = base_path or Path.cwd()
        self.component_loader = InferredComponentLoader()
        self.components: Dict[str, Dict[str, Any]] = {}
        self.main_config: Optional[TeamMainConfig] = None
        
    async def load_team_from_directory(self, team_path: Path) -> ModularTeamConfig:
        """Load team from modular directory structure."""
        logger.info(f"Loading modular team from {team_path}")
        
        # 1. Load main team configuration
        await self._load_main_config(team_path)
        
        # 2. Discover and load all components
        await self._discover_and_load_components(team_path)
        
        # 3. Apply hierarchical overrides
        await self._apply_overrides()
        
        # 4. Filter components based on include/exclude rules
        await self._filter_components()
        
        # 5. Validate component references and dependencies
        await self._validate_team_composition()
        
        # 6. Build modular team configuration
        return await self._build_modular_team_config()
    
    async def _load_main_config(self, team_path: Path):
        """Load main team configuration file."""
        main_files = [
            team_path / "main.yaml",
            team_path / "main.yml", 
            team_path / "team.yaml",
            team_path / "team.yml"
        ]
        
        main_file = None
        for file_path in main_files:
            if file_path.exists():
                main_file = file_path
                break
        
        if not main_file:
            raise ConfigurationError(f"Main configuration file not found in {team_path}. Expected: main.yaml, main.yml, team.yaml, or team.yml")
        
        try:
            with open(main_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
            
            # Resolve environment variables in main config
            data = self._resolve_environment_variables(data)
            
            # Extract main config fields
            main_fields = {'name', 'id', 'description', 'version', 'tags', 'config', 'overrides', 'components'}
            main_data = {k: v for k, v in data.items() if k in main_fields}
            
            # Capture any additional top-level configuration (like learning)
            additional_config = {k: v for k, v in data.items() if k not in main_fields}
            if additional_config:
                if 'config' not in main_data:
                    main_data['config'] = {}
                main_data['config'].update(additional_config)
                logger.debug(f"Added top-level config to main.config: {list(additional_config.keys())}")
            
            self.main_config = TeamMainConfig.model_validate(main_data)
            logger.info(f"Loaded main config: {self.main_config.name}")
            
        except Exception as e:
            raise ConfigurationError(f"Error loading main configuration from {main_file}: {e}")
    
    async def _discover_and_load_components(self, team_path: Path):
        """Discover and load all components in team directory."""
        discovered_components = await self.component_loader.discover_team_components(team_path)
        
        # Organize components by type and ID
        for component_type, component_list in discovered_components.items():
            if component_type not in self.components:
                self.components[component_type] = {}
            
            for component_data in component_list:
                component_id = component_data["id"]
                # Resolve environment variables in component data
                component_data = self._resolve_environment_variables(component_data)
                self.components[component_type][component_id] = component_data
        
        logger.info(f"Loaded components: {dict((k, len(v)) for k, v in self.components.items())}")
    
    def _resolve_environment_variables(self, data: Any) -> Any:
        """Resolve environment variables in configuration data."""
        if isinstance(data, str):
            # Pattern: ${VAR_NAME} or ${VAR_NAME:default_value}
            pattern = r'\$\{([^}:]+)(?::([^}]*))?\}'
            
            def replace_env_var(match):
                var_name = match.group(1)
                default_value = match.group(2) if match.group(2) is not None else ""
                return os.getenv(var_name, default_value)
            
            return re.sub(pattern, replace_env_var, data)
        
        elif isinstance(data, dict):
            return {k: self._resolve_environment_variables(v) for k, v in data.items()}
        
        elif isinstance(data, list):
            return [self._resolve_environment_variables(item) for item in data]
        
        else:
            return data
    
    async def _apply_overrides(self):
        """Apply hierarchical overrides from main configuration."""
        if not self.main_config or not self.main_config.overrides:
            return
        
        logger.debug("Applying configuration overrides")
        
        for component_type, type_overrides in self.main_config.overrides.items():
            if component_type in self.components:
                for component_id, component_overrides in type_overrides.items():
                    if component_id in self.components[component_type]:
                        # Deep merge overrides into component configuration
                        original = self.components[component_type][component_id]
                        overridden = self._deep_merge(original, component_overrides)
                        self.components[component_type][component_id] = overridden
                        logger.debug(f"Applied overrides to {component_type}/{component_id}")
    
    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries, with override values taking precedence."""
        result = deepcopy(base)
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = deepcopy(value)
        
        return result
    
    async def _filter_components(self):
        """Filter components based on include/exclude rules."""
        if not self.main_config or not self.main_config.components:
            return
        
        logger.debug("Applying component filters")
        
        components_config = self.main_config.components
        
        # Apply include filters
        if "include" in components_config:
            for component_type, included_ids in components_config["include"].items():
                if component_type in self.components:
                    # Keep only included components
                    filtered = {
                        comp_id: comp_data 
                        for comp_id, comp_data in self.components[component_type].items()
                        if comp_id in included_ids
                    }
                    self.components[component_type] = filtered
                    logger.debug(f"Included {len(filtered)} {component_type} components")
        
        # Apply exclude filters
        if "exclude" in components_config:
            for component_type, excluded_ids in components_config["exclude"].items():
                if component_type in self.components:
                    # Remove excluded components
                    for comp_id in excluded_ids:
                        if comp_id in self.components[component_type]:
                            del self.components[component_type][comp_id]
                            logger.debug(f"Excluded {component_type}/{comp_id}")
    
    async def _validate_team_composition(self):
        """Validate component references and dependencies."""
        logger.debug("Validating team composition")
        
        errors = []
        
        # Validate agent tool and knowledge references
        agents = self.components.get("agent", {})
        tools = self.components.get("tool", {})
        knowledge = self.components.get("knowledge", {})
        
        for agent_id, agent_data in agents.items():
            # Check tool references
            agent_tools = agent_data.get("tools", [])
            for tool_ref in agent_tools:
                if tool_ref not in tools:
                    errors.append(f"Agent '{agent_id}' references missing tool '{tool_ref}'")
            
            # Check knowledge references
            agent_knowledge = agent_data.get("knowledge", [])
            for kb_ref in agent_knowledge:
                if kb_ref not in knowledge:
                    errors.append(f"Agent '{agent_id}' references missing knowledge base '{kb_ref}'")
            
            # Check delegation references
            delegations = agent_data.get("delegation", [])
            for delegation in delegations:
                if isinstance(delegation, dict) and "agent" in delegation:
                    target_agent = delegation["agent"]
                    if target_agent not in agents:
                        errors.append(f"Agent '{agent_id}' delegates to missing agent '{target_agent}'")
        
        # Check for exactly one orchestrator
        orchestrators = [
            agent_id for agent_id, agent_data in agents.items() 
            if agent_data.get("orchestrator", False)
        ]
        if not orchestrators:
            errors.append("Team must have at least one orchestrator agent")
        elif len(orchestrators) > 1:
            errors.append(f"Team must have exactly one orchestrator agent, found {len(orchestrators)}: {', '.join(orchestrators)}")
        
        # Check for at least one agent
        if not agents:
            errors.append("Team must have at least one agent")
        
        if errors:
            raise ConfigurationError(f"Team composition validation failed:\n" + "\n".join(f"- {error}" for error in errors))
        
        logger.info("Team composition validation passed")
    
    async def _build_modular_team_config(self) -> ModularTeamConfig:
        """Build final modular team configuration."""
        logger.debug("Building modular team configuration")
        
        # Convert component data to typed configurations
        agents = {}
        for agent_id, agent_data in self.components.get("agent", {}).items():
            # Include id field, remove only file_path metadata
            clean_data = {k: v for k, v in agent_data.items() if k not in ["file_path"]}
            agents[agent_id] = AgentComponentConfig.model_validate(clean_data)
        
        tools = {}
        for tool_id, tool_data in self.components.get("tool", {}).items():
            # Include id field, remove only file_path metadata
            clean_data = {k: v for k, v in tool_data.items() if k not in ["file_path"]}
            tools[tool_id] = ToolComponentConfig.model_validate(clean_data)
        
        knowledge_bases = {}
        for kb_id, kb_data in self.components.get("knowledge", {}).items():
            # Include id, name, type fields - remove only file_path metadata
            clean_data = {k: v for k, v in kb_data.items() if k not in ["file_path"]}
            knowledge_bases[kb_id] = KnowledgeComponentConfig.model_validate(clean_data)
        
        prompts = {}
        for prompt_id, prompt_data in self.components.get("prompt", {}).items():
            # Include id field, remove only file_path metadata
            clean_data = {k: v for k, v in prompt_data.items() if k not in ["file_path"]}
            prompts[prompt_id] = PromptComponentConfig.model_validate(clean_data)
        
        trait_components = {}
        for trait_id, trait_data in self.components.get("trait", {}).items():
            # Include id field, remove only file_path metadata
            clean_data = {k: v for k, v in trait_data.items() if k not in ["file_path"]}
            trait_components[trait_id] = TraitComponentConfig.model_validate(clean_data)
        
        modular_config = ModularTeamConfig(
            main=self.main_config,
            agents=agents,
            tools=tools,
            knowledge=knowledge_bases,
            prompts=prompts,
            traits=trait_components
        )
        
        logger.info(f"Built modular team config for '{self.main_config.name}' with {len(agents)} agents, {len(tools)} tools, {len(knowledge_bases)} knowledge bases, {len(trait_components)} traits")
        return modular_config
    
    async def convert_to_legacy_format(self, modular_config: ModularTeamConfig) -> Dict[str, Any]:
        """Convert modular configuration to legacy monolithic format."""
        logger.debug("Converting modular config to legacy format")
        
        legacy_config = {
            "name": modular_config.main.name,
            "id": modular_config.main.id or modular_config.main.name.lower().replace(' ', '-'),
            "description": modular_config.main.description,
            "agents": [],
            "tools": [],
            "knowledge": [],
            "traits": []
        }
        
        # Add team-level config if present
        if modular_config.main.config:
            legacy_config.update(modular_config.main.config)
        
        # Convert agent components
        for agent_id, agent_comp in modular_config.agents.items():
            legacy_agent = {
                "id": agent_id,
                "name": agent_id,
                "instructions": agent_comp.instructions,
                "model": agent_comp.model,
                "temperature": agent_comp.temperature,
                "reasoning_effort": agent_comp.reasoning_effort,
                "orchestrator": agent_comp.orchestrator,
                "tools": agent_comp.tools or [],
                "knowledge": agent_comp.knowledge or []
            }
            
            # Add delegation if present
            if agent_comp.delegation:
                legacy_agent["delegation"] = agent_comp.delegation
            
            # Add traits if present
            if agent_comp.traits:
                legacy_traits = []
                for trait in agent_comp.traits:
                    if isinstance(trait, str):
                        # String reference - convert to legacy format by looking up trait component
                        trait_component = modular_config.traits.get(trait)
                        if trait_component:
                            legacy_traits.append({
                                "name": trait_component.name,
                                "description": trait_component.description,
                                "instructions": trait_component.instructions,
                                "weight": trait_component.weight,
                                "category": trait_component.category,
                                "tags": trait_component.tags
                            })
                        else:
                            # Fallback for missing trait component
                            legacy_traits.append({
                                "name": trait,
                                "instructions": f"Apply {trait} personality trait",
                                "weight": 1.0
                            })
                    else:
                        # TraitReference object - get base trait and apply overrides
                        trait_component = modular_config.traits.get(trait.name)
                        if trait_component:
                            legacy_trait = {
                                "name": trait_component.name,
                                "description": trait_component.description,
                                "instructions": trait_component.instructions,
                                "weight": trait.weight if trait.weight is not None else trait_component.weight,
                                "category": trait_component.category,
                                "tags": trait_component.tags
                            }
                            legacy_traits.append(legacy_trait)
                        else:
                            # Fallback for missing trait component
                            legacy_traits.append({
                                "name": trait.name,
                                "instructions": f"Apply {trait.name} personality trait",
                                "weight": trait.weight if trait.weight is not None else 1.0
                            })
                
                legacy_agent["traits"] = legacy_traits
            
            # Add learning if present
            if hasattr(agent_comp, 'learning') and agent_comp.learning:
                legacy_agent["learning"] = agent_comp.learning
            
            # Add memory if present
            if hasattr(agent_comp, 'memory') and agent_comp.memory:
                legacy_agent["memory"] = agent_comp.memory
            
            # Add listen property if present
            if hasattr(agent_comp, 'listen') and agent_comp.listen:
                legacy_agent["listen"] = agent_comp.listen
            
            # Add trigger property if present
            if hasattr(agent_comp, 'trigger') and agent_comp.trigger:
                legacy_agent["trigger"] = agent_comp.trigger
            
            legacy_config["agents"].append(legacy_agent)
        
        # Convert tool components
        for tool_id, tool_comp in modular_config.tools.items():
            legacy_tool = {
                "id": tool_id,
                "name": tool_id
            }
            
            # Add all tool fields that are present
            for field in ["module", "class_name", "url", "command", "connection_type", "args", "headers", "timeout"]:
                value = getattr(tool_comp, field, None)
                if value is not None:
                    # Keep the original field name
                    legacy_tool[field] = value
                    # Also provide class alias for backward compatibility
                    if field == "class_name":
                        legacy_tool["class"] = value
            
            legacy_config["tools"].append(legacy_tool)
        
        # Convert knowledge components
        for kb_id, kb_comp in modular_config.knowledge.items():
            legacy_kb = {
                "name": kb_id,
                "id": kb_id,  # Add id field for compatibility with knowledge loader
                "type": kb_comp.type,
                "data": kb_comp.data
            }
            
            if kb_comp.config:
                legacy_kb["config"] = kb_comp.config
            
            legacy_config["knowledge"].append(legacy_kb)
        
        # Convert trait components  
        for trait_id, trait_comp in modular_config.traits.items():
            legacy_trait = {
                "id": trait_id,
                "name": trait_comp.name,
                "description": trait_comp.description,
                "instructions": trait_comp.instructions,
                "weight": trait_comp.weight,
                "category": getattr(trait_comp, 'category', None),
                "tags": getattr(trait_comp, 'tags', [])
            }
            
            legacy_config["traits"].append(legacy_trait)
        
        logger.info(f"Converted to legacy format with {len(legacy_config['agents'])} agents, {len(legacy_config['tools'])} tools, {len(legacy_config['knowledge'])} knowledge bases, {len(legacy_config['traits'])} traits")
        return legacy_config
    
    async def add_learning_to_agent(self, team_path: Path, agent_id: str, learning_data: Dict[str, Any]) -> bool:
        """Add a new learning to an agent's configuration and persist to YAML."""
        try:
            logger.info(f"Adding learning to agent {agent_id} in team {team_path}")
            
            # Check if this is modular or monolithic config
            if (team_path / "main.yaml").exists() or (team_path / "team.yaml").exists():
                return await self._add_learning_to_modular_config(team_path, agent_id, learning_data)
            else:
                return await self._add_learning_to_monolithic_config(team_path, agent_id, learning_data)
                
        except Exception as e:
            logger.error(f"Failed to add learning to agent {agent_id}: {e}")
            return False
    
    async def _add_learning_to_modular_config(self, team_path: Path, agent_id: str, learning_data: Dict[str, Any]) -> bool:
        """Add learning to modular configuration."""
        agent_file = team_path / "agents" / f"{agent_id}.yaml"
        
        if not agent_file.exists():
            logger.error(f"Agent file not found: {agent_file}")
            return False
        
        try:
            # Load current agent configuration
            with open(agent_file, 'r', encoding='utf-8') as f:
                agent_config = yaml.safe_load(f) or {}
            
            # Initialize learning array if not present
            if 'learning' not in agent_config:
                agent_config['learning'] = []
            
            # Add new learning with timestamp
            from datetime import datetime
            new_learning = {
                **learning_data,
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat(),
                'usage_count': 0
            }
            
            agent_config['learning'].append(new_learning)
            
            # Write back to file
            with open(agent_file, 'w', encoding='utf-8') as f:
                yaml.dump(agent_config, f, default_flow_style=False, allow_unicode=True)
            
            logger.info(f"Added learning to modular agent {agent_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update modular agent config: {e}")
            return False
    
    async def _add_learning_to_monolithic_config(self, config_file: Path, agent_id: str, learning_data: Dict[str, Any]) -> bool:
        """Add learning to monolithic configuration."""
        try:
            # Load current team configuration
            with open(config_file, 'r', encoding='utf-8') as f:
                team_config = yaml.safe_load(f) or {}
            
            # Find the agent in the configuration
            agents = team_config.get('agents', [])
            agent_found = False
            
            for agent in agents:
                if agent.get('name') == agent_id:
                    # Initialize learning array if not present
                    if 'learning' not in agent:
                        agent['learning'] = []
                    
                    # Add new learning with timestamp
                    from datetime import datetime
                    new_learning = {
                        **learning_data,
                        'created_at': datetime.utcnow().isoformat(),
                        'updated_at': datetime.utcnow().isoformat(),
                        'usage_count': 0
                    }
                    
                    agent['learning'].append(new_learning)
                    agent_found = True
                    break
            
            if not agent_found:
                logger.error(f"Agent {agent_id} not found in team configuration")
                return False
            
            # Write back to file
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(team_config, f, default_flow_style=False, allow_unicode=True)
            
            logger.info(f"Added learning to monolithic agent {agent_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update monolithic team config: {e}")
            return False