"""
Team configuration splitter for converting monolithic YAML to modular format.

This module provides functionality to split existing monolithic team configurations
into modular directory-based components.
"""
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class TeamConfigurationSplitter:
    """Splits monolithic team configurations into modular components."""
    
    def __init__(self):
        self.component_dirs = {
            "agents": "agents",
            "tools": "tools", 
            "knowledge": "knowledge",
            "prompts": "prompts",
            "traits": "traits"
        }
        self.extracted_traits = {}  # Track extracted traits to avoid duplicates
    
    async def split_configuration(self, yaml_file: Path, output_dir: Path):
        """Split monolithic YAML into modular directory structure."""
        logger.info(f"Splitting {yaml_file} into modular format at {output_dir}")
        
        # Load original configuration
        with open(yaml_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        if not isinstance(config, dict):
            raise ValueError("Configuration must be a dictionary")
        
        # Create output directory structure
        await self._create_directory_structure(output_dir)
        
        # Split components
        await self._extract_traits_from_agents(config.get("agents", []), output_dir)
        await self._split_agents(config.get("agents", []), output_dir)
        await self._split_tools(config.get("tools", []), output_dir)
        await self._split_knowledge(config.get("knowledge", []), output_dir)
        
        # Create main configuration
        await self._create_main_config(config, output_dir)
        
        logger.info(f"Successfully split configuration into {output_dir}")
    
    async def _create_directory_structure(self, output_dir: Path):
        """Create modular directory structure."""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for dir_name in self.component_dirs.values():
            (output_dir / dir_name).mkdir(exist_ok=True)
        
        logger.debug(f"Created directory structure in {output_dir}")
    
    async def _split_agents(self, agents: List[Dict[str, Any]], output_dir: Path):
        """Split agent configurations into individual files."""
        agents_dir = output_dir / "agents"
        
        for agent in agents:
            if not isinstance(agent, dict):
                continue
                
            agent_name = agent.get("name", "unnamed_agent")
            agent_id = self._sanitize_filename(agent_name)
            
            # Extract agent-specific configuration
            agent_config = {
                "instructions": agent.get("instructions", ""),
                "model": agent.get("model", "gpt-4o"),
                "temperature": agent.get("temperature", 0.7),
                "reasoning_effort": agent.get("reasoning_effort", "medium"),
                "orchestrator": agent.get("orchestrator", False)
            }
            
            # Add optional fields if present
            optional_fields = ["tools", "knowledge", "delegation"]
            for field in optional_fields:
                if field in agent and agent[field]:
                    agent_config[field] = agent[field]
            
            # Handle traits conversion from inline to references
            if "traits" in agent and agent["traits"]:
                agent_config["traits"] = self._convert_traits_to_references(agent["traits"])
            
            # Write agent configuration file
            agent_file = agents_dir / f"{agent_id}.yaml"
            await self._write_yaml_file(agent_file, agent_config)
            
            logger.debug(f"Created agent component: {agent_id}")
    
    async def _extract_traits_from_agents(self, agents: List[Dict[str, Any]], output_dir: Path):
        """Extract inline traits from agents and create separate trait components."""
        traits_dir = output_dir / "traits"
        
        for agent in agents:
            if not isinstance(agent, dict):
                continue
                
            traits = agent.get("traits", [])
            if not traits:
                continue
                
            for trait in traits:
                # Skip if it's just a string reference (already modular)
                if isinstance(trait, str):
                    continue
                    
                # Extract inline trait definition
                if isinstance(trait, dict) and "name" in trait:
                    trait_name = trait["name"]
                    trait_id = self._sanitize_filename(trait_name)
                    
                    # Skip if we've already extracted this trait
                    if trait_id in self.extracted_traits:
                        continue
                    
                    # Create trait component configuration
                    trait_config = {
                        "name": trait_name,
                        "instructions": trait.get("instructions", ""),
                        "weight": trait.get("weight", 1.0)
                    }
                    
                    # Add optional fields if present
                    optional_fields = ["description", "category", "tags"]
                    for field in optional_fields:
                        if field in trait and trait[field]:
                            trait_config[field] = trait[field]
                    
                    # Write trait component file
                    trait_file = traits_dir / f"{trait_id}.yaml"
                    await self._write_yaml_file(trait_file, trait_config)
                    
                    # Track extracted trait
                    self.extracted_traits[trait_id] = trait_config
                    logger.debug(f"Extracted trait component: {trait_id}")
    
    def _convert_traits_to_references(self, traits: List) -> List:
        """Convert inline trait definitions to modular references."""
        converted_traits = []
        
        for trait in traits:
            if isinstance(trait, str):
                # Already a reference, keep as-is
                converted_traits.append(trait)
            elif isinstance(trait, dict) and "name" in trait:
                # Convert inline trait to reference
                trait_name = trait["name"]
                
                # If trait has custom weight, preserve as object reference
                if "weight" in trait and trait["weight"] != self.extracted_traits.get(self._sanitize_filename(trait_name), {}).get("weight", 1.0):
                    converted_traits.append({
                        "name": trait_name,
                        "weight": trait["weight"]
                    })
                else:
                    # Use simple string reference
                    converted_traits.append(trait_name)
        
        return converted_traits
    
    async def _split_tools(self, tools: List[Dict[str, Any]], output_dir: Path):
        """Split tool configurations into individual files."""
        tools_dir = output_dir / "tools"
        
        for tool in tools:
            if not isinstance(tool, dict):
                continue
                
            tool_name = tool.get("name", "unnamed_tool")
            tool_id = self._sanitize_filename(tool_name)
            
            # Extract tool-specific configuration
            tool_config = {}
            
            # Add all tool fields except name (which becomes the filename)
            for key, value in tool.items():
                if key != "name" and value is not None:
                    tool_config[key] = value
            
            # Write tool configuration file
            tool_file = tools_dir / f"{tool_id}.yaml"
            await self._write_yaml_file(tool_file, tool_config)
            
            logger.debug(f"Created tool component: {tool_id}")
    
    async def _split_knowledge(self, knowledge: List[Dict[str, Any]], output_dir: Path):
        """Split knowledge base configurations into individual files."""
        knowledge_dir = output_dir / "knowledge"
        
        for kb in knowledge:
            if not isinstance(kb, dict):
                continue
                
            kb_name = kb.get("name", "unnamed_knowledge")
            kb_id = self._sanitize_filename(kb_name)
            
            # Extract knowledge-specific configuration
            kb_config = {
                "type": kb.get("type", "text"),
                "data": kb.get("data", [])
            }
            
            # Add optional config if present
            if "config" in kb and kb["config"]:
                kb_config["config"] = kb["config"]
            
            # Write knowledge configuration file
            kb_file = knowledge_dir / f"{kb_id}.yaml"
            await self._write_yaml_file(kb_file, kb_config)
            
            logger.debug(f"Created knowledge component: {kb_id}")
    
    async def _create_main_config(self, original_config: Dict[str, Any], output_dir: Path):
        """Create main team configuration file."""
        main_config = {
            "name": original_config.get("name", "Untitled Team"),
            "description": original_config.get("description"),
            "version": "1.0.0"
        }
        
        # Add team-level configuration (exclude component arrays)
        excluded_keys = {"name", "description", "agents", "tools", "knowledge", "traits"}
        team_config = {
            k: v for k, v in original_config.items() 
            if k not in excluded_keys and v is not None
        }
        
        if team_config:
            main_config["config"] = team_config
        
        # Add placeholder for overrides and component filters
        main_config["overrides"] = {}
        
        # Add components section with extracted traits
        components = {}
        if self.extracted_traits:
            components["traits"] = list(self.extracted_traits.keys())
        
        main_config["components"] = components
        
        # Write main configuration file
        main_file = output_dir / "main.yaml"
        await self._write_yaml_file(main_file, main_config)
        
        logger.debug("Created main configuration file")
    
    async def _write_yaml_file(self, file_path: Path, data: Dict[str, Any]):
        """Write data to YAML file with proper formatting."""
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False, indent=2)
    
    def _sanitize_filename(self, name: str) -> str:
        """Sanitize string for use as filename."""
        # Replace spaces and special characters with hyphens
        import re
        sanitized = re.sub(r'[^\w\-_]', '-', name.lower())
        # Remove multiple consecutive hyphens
        sanitized = re.sub(r'-+', '-', sanitized)
        # Remove leading/trailing hyphens
        return sanitized.strip('-')


class TeamConfigurationMerger:
    """Merges modular team configurations back to monolithic format."""
    
    async def merge_configuration(self, team_dir: Path, output_file: Path):
        """Merge modular components into monolithic YAML."""
        logger.info(f"Merging modular team from {team_dir} to {output_file}")
        
        from .configuration_manager import ConfigurationManager
        
        # Load modular configuration
        config_manager = ConfigurationManager()
        modular_config = await config_manager.load_team_from_directory(team_dir)
        
        # Convert to legacy format
        legacy_config = await config_manager.convert_to_legacy_format(modular_config)
        
        # Write merged configuration
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            yaml.dump(legacy_config, f, default_flow_style=False, sort_keys=False, indent=2)
        
        logger.info(f"Successfully merged configuration to {output_file}")