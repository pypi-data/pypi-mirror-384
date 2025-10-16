"""YAML configuration updater utility for learning system."""

import os
import shutil
import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

import yaml
from ..schemas.learning import LearningError
from ..utils.logging import get_logger

logger = get_logger(__name__)


class YamlUpdater:
    """Utility for safely updating YAML configuration files."""
    
    def __init__(self, backup_enabled: bool = True):
        """Initialize YAML updater.
        
        Args:
            backup_enabled: Whether to create backups before updating files
        """
        self.backup_enabled = backup_enabled
    
    async def update_agent_instructions(self, 
                                      team_path: str, 
                                      agent_name: str, 
                                      new_instructions: str) -> Optional[str]:
        """Update agent instructions in team configuration.
        
        Args:
            team_path: Path to team configuration file or directory
            agent_name: Name of the agent to update
            new_instructions: New instructions text
            
        Returns:
            Optional[str]: Backup file path if backup was created
            
        Raises:
            LearningError: If update fails
        """
        try:
            # Determine if it's a file or directory configuration
            path = Path(team_path)
            backup_path = None
            if path.is_file():
                backup_path = await self._update_monolithic_config(path, agent_name, new_instructions)
            elif path.is_dir():
                backup_path = await self._update_modular_config(path, agent_name, new_instructions)
            else:
                raise LearningError(f"Team path does not exist: {team_path}", "INVALID_TEAM_PATH")
                
            logger.info(f"Successfully updated instructions for agent {agent_name}")
            return backup_path
            
        except LearningError:
            raise
        except Exception as e:
            logger.error(f"Failed to update agent instructions: {e}")
            raise LearningError(f"YAML update failed: {e}", "YAML_UPDATE_ERROR")
    
    async def update_agent_memory(self, 
                                team_path: str, 
                                agent_name: str, 
                                new_memory: Dict[str, Any]) -> Optional[str]:
        """Update agent memory in team configuration.
        
        Args:
            team_path: Path to team configuration file or directory
            agent_name: Name of the agent to update
            new_memory: New memory dictionary to merge/replace
            
        Returns:
            Optional[str]: Backup file path if backup was created
            
        Raises:
            LearningError: If update fails
        """
        try:
            # Determine if it's a file or directory configuration
            path = Path(team_path)
            backup_path = None
            if path.is_file():
                backup_path = await self._update_monolithic_memory(path, agent_name, new_memory)
            elif path.is_dir():
                backup_path = await self._update_modular_memory(path, agent_name, new_memory)
            else:
                raise LearningError(f"Team path does not exist: {team_path}", "INVALID_TEAM_PATH")
                
            logger.info(f"Successfully updated memory for agent {agent_name}")
            return backup_path
            
        except LearningError:
            raise
        except Exception as e:
            logger.error(f"Failed to update agent memory: {e}")
            raise LearningError(f"Memory update failed: {e}", "MEMORY_UPDATE_ERROR")
    
    async def _update_monolithic_config(self, 
                                      config_path: Path, 
                                      agent_name: str, 
                                      new_instructions: str) -> Optional[str]:
        """Update agent instructions in monolithic YAML file.
        
        Args:
            config_path: Path to the YAML configuration file
            agent_name: Name of the agent to update
            new_instructions: New instructions text
        """
        backup_path = self._create_backup_if_enabled(config_path)
        
        try:
            config = self._load_yaml_file(config_path)
            agents = config.get('agents', [])
            
            def update_agent_instructions(agent: dict, index: int) -> None:
                config['agents'][index]['instructions'] = new_instructions
                self._update_learning_metadata(config['agents'][index], 'last_learning_update')
                logger.debug(f"Updated agent {agent_name} instructions")
            
            agent_updated = self._find_and_update_agent_in_list(agents, agent_name, update_agent_instructions)
            
            if not agent_updated:
                raise LearningError(f"Agent {agent_name} not found in configuration", "AGENT_NOT_FOUND")
            
            self._save_yaml_file(config_path, config)
            return backup_path
            
        except Exception as e:
            self._restore_backup_on_failure(config_path, backup_path)
            raise
    
    async def _update_modular_config(self, 
                                   config_dir: Path, 
                                   agent_name: str, 
                                   new_instructions: str) -> Optional[str]:
        """Update agent instructions in modular configuration directory.
        
        Args:
            config_dir: Path to the configuration directory
            agent_name: Name of the agent to update
            new_instructions: New instructions text
        """
        agent_file = self._find_agent_file(config_dir, agent_name)
        if not agent_file:
            raise LearningError(f"Agent {agent_name} configuration not found in {config_dir}", "AGENT_CONFIG_NOT_FOUND")
        
        backup_path = self._create_backup_if_enabled(agent_file)
        
        try:
            agent_config = self._load_yaml_file(agent_file)
            agent_config['instructions'] = new_instructions
            self._update_learning_metadata(agent_config, 'last_learning_update')
            
            logger.debug(f"Saving instructions content (first 200 chars): {new_instructions[:200]}")
            logger.debug(f"Instructions contains newlines: {'\n' in new_instructions}")
            logger.debug(f"Instructions length: {len(new_instructions)}")
            
            self._save_yaml_file(agent_file, agent_config)
            logger.debug(f"Updated agent {agent_name} in modular configuration")
            return backup_path
            
        except Exception as e:
            self._restore_backup_on_failure(agent_file, backup_path)
            raise
    
    async def _update_monolithic_memory(self, 
                                      config_path: Path, 
                                      agent_name: str, 
                                      new_memory: Dict[str, Any]) -> Optional[str]:
        """Update agent memory in monolithic YAML file.
        
        Args:
            config_path: Path to the YAML configuration file
            agent_name: Name of the agent to update
            new_memory: New memory dictionary to merge/replace
        """
        backup_path = self._create_backup_if_enabled(config_path)
        
        try:
            config = self._load_yaml_file(config_path)
            agents = config.get('agents', [])
            
            def update_agent_memory(agent: dict, index: int) -> None:
                existing_memory = agent.get('memory', {})
                merged_memory = self._merge_memory(existing_memory, new_memory)
                config['agents'][index]['memory'] = merged_memory
                self._update_learning_metadata(config['agents'][index], 'last_memory_update')
                logger.debug(f"Updated agent {agent_name} memory")
            
            agent_updated = self._find_and_update_agent_in_list(agents, agent_name, update_agent_memory)
            
            if not agent_updated:
                raise LearningError(f"Agent {agent_name} not found in configuration", "AGENT_NOT_FOUND")
            
            self._save_yaml_file(config_path, config)
            return backup_path
            
        except Exception as e:
            self._restore_backup_on_failure(config_path, backup_path)
            raise
    
    async def _update_modular_memory(self, 
                                   config_dir: Path, 
                                   agent_name: str, 
                                   new_memory: Dict[str, Any]) -> Optional[str]:
        """Update agent memory in modular configuration directory.
        
        Args:
            config_dir: Path to the configuration directory
            agent_name: Name of the agent to update
            new_memory: New memory dictionary to merge/replace
        """
        agent_file = self._find_agent_file(config_dir, agent_name)
        if not agent_file:
            raise LearningError(f"Agent {agent_name} configuration not found in {config_dir}", "AGENT_CONFIG_NOT_FOUND")
        
        backup_path = self._create_backup_if_enabled(agent_file)
        
        try:
            agent_config = self._load_yaml_file(agent_file)
            existing_memory = agent_config.get('memory', {})
            merged_memory = self._merge_memory(existing_memory, new_memory)
            
            agent_config['memory'] = merged_memory
            self._update_learning_metadata(agent_config, 'last_memory_update')
            
            logger.debug(f"Saving memory content for {agent_name}: {merged_memory}")
            self._save_yaml_file(agent_file, agent_config)
            logger.debug(f"Updated agent {agent_name} memory in modular configuration")
            return backup_path
            
        except Exception as e:
            self._restore_backup_on_failure(agent_file, backup_path)
            raise
    
    def _merge_memory(self, existing_memory: Any, new_memory: Any) -> Any:
        """Merge memory content supporting both dict and string formats.
        
        Args:
            existing_memory: Current agent memory (dict, string, or None)
            new_memory: New memory to merge (dict, string, or None)
            
        Returns:
            Merged memory in appropriate format
        """
        # If new memory is None or empty, keep existing
        if new_memory is None or new_memory == "" or new_memory == {}:
            return existing_memory or {}
        
        # If existing memory is None or empty, use new memory
        if existing_memory is None or existing_memory == "" or existing_memory == {}:
            return new_memory
        
        # If both are dictionaries, merge them (new takes precedence)
        if isinstance(existing_memory, dict) and isinstance(new_memory, dict):
            return {**existing_memory, **new_memory}
        
        # If new memory is a string, use it directly (replaces existing)
        if isinstance(new_memory, str):
            return new_memory
        
        # If new memory is a dict but existing is a string, replace with dict
        if isinstance(new_memory, dict) and isinstance(existing_memory, str):
            return new_memory
        
        # Default: new memory takes precedence
        return new_memory
    
    def _create_backup_if_enabled(self, file_path: Path) -> Optional[Path]:
        """Create backup if backup is enabled.
        
        Args:
            file_path: Path to file to backup
            
        Returns:
            Backup path if created, None otherwise
        """
        if not self.backup_enabled:
            return None
            
        backup_path = self._create_backup(file_path)
        logger.debug(f"Created backup: {backup_path}")
        return backup_path
    
    def _restore_backup_on_failure(self, original_path: Path, backup_path: Optional[Path]) -> None:
        """Restore backup if it exists and backup is enabled.
        
        Args:
            original_path: Path to original file to restore
            backup_path: Path to backup file, if any
        """
        if self.backup_enabled and backup_path:
            try:
                shutil.copy2(backup_path, original_path)
                logger.info(f"Restored backup due to update failure")
            except Exception as restore_error:
                logger.error(f"Failed to restore backup: {restore_error}")
    
    def _update_learning_metadata(self, config: dict, field_name: str) -> None:
        """Update learning metadata in agent configuration.
        
        Args:
            config: Agent configuration dictionary
            field_name: Name of the metadata field to update ('last_learning_update' or 'last_memory_update')
        """
        config.setdefault('metadata', {})
        config['metadata'][field_name] = datetime.utcnow().isoformat()
        config['metadata']['learning_source'] = 'automated_learning'
    
    def _find_and_update_agent_in_list(self, agents: list, agent_name: str, update_func) -> bool:
        """Find agent in list and apply update function.
        
        Args:
            agents: List of agent configurations
            agent_name: Name of agent to find
            update_func: Function to call with (agent_config, index) when agent found
            
        Returns:
            True if agent was found and updated, False otherwise
        """
        for i, agent in enumerate(agents):
            if self._agent_matches(agent, agent_name):
                update_func(agent, i)
                return True
        return False
    
    def _agent_matches(self, agent: dict, agent_name: str) -> bool:
        """Check if agent configuration matches the given agent name.
        
        Args:
            agent: Agent configuration dictionary
            agent_name: Name to match against
            
        Returns:
            True if agent matches, False otherwise
        """
        agent_id = agent.get('id')
        agent_name_field = agent.get('name')
        
        return (agent_name_field == agent_name or 
                agent_id == agent_name or 
                (agent_name_field and agent_name_field.lower().replace(' ', '_') == agent_name.lower()))
    
    def _find_agent_file(self, config_dir: Path, agent_name: str) -> Optional[Path]:
        """Find agent configuration file in modular directory structure.
        
        Args:
            config_dir: Configuration directory path
            agent_name: Name of the agent
            
        Returns:
            Path to agent file or None if not found
        """
        # Try common patterns for agent files
        patterns = [
            f"agents/{agent_name}.yaml",
            f"agents/{agent_name}.yml",
            f"{agent_name}.yaml",
            f"{agent_name}.yml"
        ]
        
        for pattern in patterns:
            agent_path = config_dir / pattern
            if agent_path.exists():
                return agent_path
        
        # Search recursively for agent files
        for yaml_file in config_dir.rglob("*.yaml"):
            try:
                config = self._load_yaml_file(yaml_file)
                if isinstance(config, dict) and config.get('name') == agent_name:
                    return yaml_file
            except Exception:
                continue  # Skip invalid YAML files
        
        for yml_file in config_dir.rglob("*.yml"):
            try:
                config = self._load_yaml_file(yml_file)
                if isinstance(config, dict) and config.get('name') == agent_name:
                    return yml_file
            except Exception:
                continue  # Skip invalid YAML files
        
        return None
    
    def _load_yaml_file(self, file_path: Path) -> Dict[str, Any]:
        """Load YAML file safely.
        
        Args:
            file_path: Path to YAML file
            
        Returns:
            Parsed YAML content
            
        Raises:
            LearningError: If file cannot be loaded
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = yaml.safe_load(f)
                
            if content is None:
                raise LearningError(f"YAML file is empty: {file_path}", "EMPTY_YAML_FILE")
                
            return content
            
        except yaml.YAMLError as e:
            raise LearningError(f"Invalid YAML syntax in {file_path}: {e}", "INVALID_YAML_SYNTAX")
        except FileNotFoundError:
            raise LearningError(f"Configuration file not found: {file_path}", "CONFIG_FILE_NOT_FOUND")
        except Exception as e:
            raise LearningError(f"Failed to load YAML file {file_path}: {e}", "YAML_LOAD_ERROR")
    
    def _save_yaml_file(self, file_path: Path, content: Dict[str, Any]) -> None:
        """Save content to YAML file safely with proper block scalar formatting.
        
        Args:
            file_path: Path to YAML file
            content: Content to save
            
        Raises:
            LearningError: If file cannot be saved
        """
        try:
            # Ensure directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Define a function to represent strings with block scalars
            def represent_literal_str(dumper, data):
                # Force literal block scalar (|) for ANY content with newlines
                # This ensures instructions are always properly formatted
                if '\n' in data:
                    # Use |- to strip final newlines for cleaner output
                    return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|-')
                # For long single-line content, use folded block scalar  
                elif len(data) > 80:
                    return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='>')
                # For short content, use default (quoted if needed)
                return dumper.represent_scalar('tag:yaml.org,2002:str', data)
            
            # Create a custom dumper class
            class FormattingDumper(yaml.SafeDumper):
                pass
            
            # Add the custom string representer for all string types
            FormattingDumper.add_representer(str, represent_literal_str)
            
            # Ensure no other representers override ours
            FormattingDumper.yaml_representers = FormattingDumper.yaml_representers.copy()
            FormattingDumper.yaml_representers[str] = represent_literal_str
            
            # Write with proper formatting preserving newlines
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(
                    content, 
                    f, 
                    Dumper=FormattingDumper,
                    default_flow_style=False,
                    sort_keys=False,
                    allow_unicode=True,
                    indent=2,
                    width=None,  # Don't wrap lines
                    encoding=None,  # Use unicode
                    explicit_start=False,
                    explicit_end=False,
                    default_style=None
                )
                
        except Exception as e:
            raise LearningError(f"Failed to save YAML file {file_path}: {e}", "YAML_SAVE_ERROR")
    
    def _create_backup(self, file_path: Path) -> Path:
        """Create backup of file in professional history structure.
        
        Args:
            file_path: Path to file to backup
            
        Returns:
            Path to backup file
            
        Raises:
            LearningError: If backup creation fails
        """
        try:
            # Determine team root directory
            team_root = self._find_team_root(file_path)
            
            # Create professional backup structure
            timestamp = datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")
            agent_name = file_path.stem
            
            # Create backup directory structure: teams/your-team/.learning/history/agents/agent_name/
            backup_dir = team_root / ".learning" / "history" / "agents" / agent_name
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Backup file with timestamp
            backup_filename = f"{timestamp}_backup.yaml"
            backup_path = backup_dir / backup_filename
            
            # Copy file to backup location
            shutil.copy2(file_path, backup_path)
            
            # Update metadata
            self._update_backup_metadata(backup_dir, backup_path, file_path)
            
            # Cleanup old backups if needed
            self._cleanup_agent_backups(backup_dir, max_backups=10)
            
            logger.info(f"Created backup: {backup_path}")
            return backup_path
            
        except Exception as e:
            logger.warning(f"Failed to create backup for {file_path}: {e}")
            # Don't fail the operation for backup issues, just log
            raise LearningError(f"Backup creation failed: {e}", "BACKUP_ERROR")
    
    def cleanup_old_backups(self, 
                           config_path: Path, 
                           max_backups: int = 10) -> None:
        """Clean up old backup files using professional backup structure.
        
        Args:
            config_path: Path to original configuration file
            max_backups: Maximum number of backups to keep
        """
        try:
            # Find team root and determine backup directory
            team_root = self._find_team_root(config_path)
            agent_name = config_path.stem
            backup_dir = team_root / ".learning" / "history" / "agents" / agent_name
            
            if backup_dir.exists():
                self._cleanup_agent_backups(backup_dir, max_backups)
            else:
                logger.debug(f"No backup directory found for agent {agent_name}")
                        
        except Exception as e:
            logger.warning(f"Failed to cleanup old backups: {e}")
    
    async def validate_configuration(self, team_path: str) -> bool:
        """Validate team configuration structure.
        
        Args:
            team_path: Path to team configuration
            
        Returns:
            True if configuration is valid
            
        Raises:
            LearningError: If configuration is invalid
        """
        try:
            path = Path(team_path)
            
            if path.is_file():
                # Validate monolithic configuration
                config = self._load_yaml_file(path)
                return self._validate_monolithic_structure(config)
                
            elif path.is_dir():
                # Validate modular configuration
                return self._validate_modular_structure(path)
                
            else:
                raise LearningError(f"Invalid team path: {team_path}", "INVALID_TEAM_PATH")
                
        except LearningError:
            raise
        except Exception as e:
            raise LearningError(f"Configuration validation failed: {e}", "VALIDATION_ERROR")
    
    def _validate_monolithic_structure(self, config: Dict[str, Any]) -> bool:
        """Validate monolithic configuration structure."""
        required_fields = ['name', 'agents']
        
        for field in required_fields:
            if field not in config:
                raise LearningError(f"Missing required field: {field}", "MISSING_REQUIRED_FIELD")
        
        agents = config.get('agents', [])
        if not isinstance(agents, list) or not agents:
            raise LearningError("Configuration must have at least one agent", "NO_AGENTS_CONFIGURED")
        
        # Validate each agent
        for i, agent in enumerate(agents):
            if not isinstance(agent, dict):
                raise LearningError(f"Agent {i} must be a dictionary", "INVALID_AGENT_STRUCTURE")
            
            if 'name' not in agent:
                raise LearningError(f"Agent {i} missing required 'name' field", "MISSING_AGENT_NAME")
        
        return True
    
    def _validate_modular_structure(self, config_dir: Path) -> bool:
        """Validate modular configuration structure."""
        # Check for team configuration file
        team_files = list(config_dir.glob("team.*")) + list(config_dir.glob("config.*"))
        if not team_files:
            raise LearningError("No team configuration file found", "NO_TEAM_CONFIG")
        
        # Check for agents directory or agent files
        agent_files = list(config_dir.rglob("*agent*.yaml")) + list(config_dir.rglob("*agent*.yml"))
        agents_dir = config_dir / "agents"
        
        if not agent_files and not agents_dir.exists():
            raise LearningError("No agent configurations found", "NO_AGENT_CONFIGS")
        
        return True
    
    def _find_team_root(self, file_path: Path) -> Path:
        """Find the team root directory for backup organization.
        
        Args:
            file_path: Path to the agent file
            
        Returns:
            Path to team root directory
        """
        current_path = file_path.parent
        
        # Look for common team configuration files going up the directory tree
        team_config_patterns = [
            'main.yaml', 'main.yml', 'team.yaml', 'team.yml', 
            'config.yaml', 'config.yml'
        ]
        
        # Check current directory and parent directories
        for _ in range(5):  # Limit search depth
            for pattern in team_config_patterns:
                if (current_path / pattern).exists():
                    return current_path
            
            # If current directory is named 'agents', check parent for team config
            if current_path.name == 'agents':
                parent = current_path.parent
                for pattern in team_config_patterns:
                    if (parent / pattern).exists():
                        return parent
                # If no team config in parent but parent has an agents directory, it's likely team root
                if (parent / 'agents').exists():
                    return parent
            
            # Check if this directory contains agents directory (likely team root)
            if (current_path / 'agents').exists():
                return current_path
            
            parent = current_path.parent
            if parent == current_path:  # Reached filesystem root
                break
            current_path = parent
        
        # Fallback to the directory containing the agent file
        return file_path.parent
    
    def _update_backup_metadata(self, 
                              backup_dir: Path, 
                              backup_path: Path, 
                              original_path: Path) -> None:
        """Update backup metadata for tracking and management.
        
        Args:
            backup_dir: Directory containing backups
            backup_path: Path to the backup file
            original_path: Path to the original file
        """
        try:
            metadata_file = backup_dir / "metadata.json"
            
            # Load existing metadata or create new
            metadata = {}
            if metadata_file.exists():
                try:
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                except Exception:
                    metadata = {}  # Reset if corrupted
            
            # Initialize structure
            if 'backups' not in metadata:
                metadata['backups'] = []
            
            if 'agent_info' not in metadata:
                metadata['agent_info'] = {
                    'name': original_path.stem,
                    'original_path': str(original_path),
                    'first_backup': datetime.utcnow().isoformat()
                }
            
            # Add backup entry
            backup_entry = {
                'timestamp': datetime.utcnow().isoformat(),
                'backup_file': backup_path.name,
                'original_size': original_path.stat().st_size if original_path.exists() else 0,
                'backup_size': backup_path.stat().st_size,
                'learning_trigger': True  # Indicates this was created during learning
            }
            
            metadata['backups'].append(backup_entry)
            metadata['last_backup'] = backup_entry['timestamp']
            metadata['total_backups'] = len(metadata['backups'])
            
            # Save metadata
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, default=str)
                
        except Exception as e:
            logger.warning(f"Failed to update backup metadata: {e}")
    
    def _cleanup_agent_backups(self, backup_dir: Path, max_backups: int = 10) -> None:
        """Clean up old backups for an agent, keeping the most recent ones.
        
        Args:
            backup_dir: Directory containing agent backups
            max_backups: Maximum number of backups to retain
        """
        try:
            # Find all backup files
            backup_files = list(backup_dir.glob("*_backup.yaml"))
            
            if len(backup_files) <= max_backups:
                return  # No cleanup needed
            
            # Sort by modification time (oldest first)
            backup_files.sort(key=lambda x: x.stat().st_mtime)
            
            # Remove oldest backups
            files_to_remove = backup_files[:-max_backups]
            
            for old_backup in files_to_remove:
                try:
                    old_backup.unlink()
                    logger.debug(f"Removed old backup: {old_backup}")
                except Exception as e:
                    logger.warning(f"Failed to remove old backup {old_backup}: {e}")
            
            # Update metadata to reflect cleanup
            try:
                metadata_file = backup_dir / "metadata.json"
                if metadata_file.exists():
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                    
                    # Remove metadata entries for deleted files
                    removed_files = {f.name for f in files_to_remove}
                    metadata['backups'] = [
                        backup for backup in metadata.get('backups', [])
                        if backup.get('backup_file') not in removed_files
                    ]
                    metadata['total_backups'] = len(metadata['backups'])
                    
                    with open(metadata_file, 'w', encoding='utf-8') as f:
                        json.dump(metadata, f, indent=2, default=str)
                        
            except Exception as e:
                logger.warning(f"Failed to update metadata after cleanup: {e}")
                
        except Exception as e:
            logger.warning(f"Failed to cleanup old backups: {e}")