"""Local YAML file-based learning storage implementation."""

import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from .base import BaseLearningStorage
from ..utils.logging import get_logger

logger = get_logger(__name__)


class LocalYAMLLearningStorage(BaseLearningStorage):
    """Learning storage implementation using local YAML files."""
    
    def store_learning(self, session: Dict[str, Any], data: Dict[str, Any]) -> bool:
        """Store learning data in the agent's YAML file.
        
        Args:
            session: Session information containing team and agent identifiers
            data: Learning data to store
            
        Returns:
            bool: True if learning was successfully stored, False otherwise
        """
        try:
            # Extract team and agent identifiers
            team_identifier = session.get("team_identifier")
            agent_identifier = session.get("agent_identifier")
            
            if not team_identifier or not agent_identifier:
                logger.error(f"Missing team_identifier ({team_identifier}) or agent_identifier ({agent_identifier})")
                return False
            
            # Find team directory
            team_dir = self._find_team_directory(team_identifier)
            if not team_dir:
                logger.error(f"Team directory not found for team_identifier: {team_identifier}")
                return False
            
            # Find agent YAML file
            agent_file = self._find_agent_file(team_dir, agent_identifier)
            if not agent_file:
                logger.error(f"Agent file not found for agent_identifier: {agent_identifier} in team: {team_identifier}")
                return False
            
            # Create learning entry
            learning_entry = self._create_learning_entry(data)
            
            # Add learning to agent YAML file
            return self._add_learning_to_yaml_file(agent_file, learning_entry)
            
        except Exception as e:
            logger.error(f"Error in LocalYAMLLearningStorage.store_learning: {e}")
            return False
    
    def _find_team_directory(self, team_identifier: str) -> Optional[Path]:
        """Find the team directory by team_identifier.
        
        Args:
            team_identifier: The team identifier to search for
            
        Returns:
            Path: Path to team directory if found, None otherwise
        """
        teams_base_dir = Path(__file__).parent.parent.parent.parent.parent / "teams"
        logger.debug(f"Teams base dir calculated as: {teams_base_dir}")
        team_dir = teams_base_dir / team_identifier
        
        if team_dir.exists() and team_dir.is_dir():
            logger.debug(f"Found team directory: {team_dir}")
            return team_dir
        
        # If direct lookup fails, try searching all team directories
        logger.debug(f"Direct lookup failed for {team_identifier}, searching all team directories...")
        for potential_dir in teams_base_dir.iterdir():
            if potential_dir.is_dir() and potential_dir.name == team_identifier:
                logger.debug(f"Found team directory via search: {potential_dir}")
                return potential_dir
        
        # If still not found, try checking if team_identifier contains path-like structure
        if "/" in team_identifier:
            # Extract the directory name from path-like identifier
            path_parts = team_identifier.split("/")
            for part in reversed(path_parts):  # Try from most specific to least
                if part:  # Skip empty parts
                    team_dir = teams_base_dir / part
                    if team_dir.exists() and team_dir.is_dir():
                        logger.debug(f"Found team directory from path part '{part}': {team_dir}")
                        return team_dir
        
        logger.warning(f"Team directory not found for identifier: {team_identifier}")
        return None
    
    def _find_agent_file(self, team_dir: Path, agent_identifier: str) -> Optional[Path]:
        """Find the agent YAML file in the team directory.
        
        Args:
            team_dir: Path to the team directory
            agent_identifier: The agent identifier to search for
            
        Returns:
            Path: Path to agent YAML file if found, None otherwise
        """
        agents_dir = team_dir / "agents"
        if not agents_dir.exists():
            logger.warning(f"Agents directory not found: {agents_dir}")
            return None
        
        # Try exact filename match first
        agent_file = agents_dir / f"{agent_identifier}.yaml"
        if agent_file.exists():
            logger.debug(f"Found agent file: {agent_file}")
            return agent_file
        
        # Search through all YAML files in agents directory
        for yaml_file in agents_dir.glob("*.yaml"):
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    agent_config = yaml.safe_load(f)
                    
                # Check if the name field matches the agent_identifier
                if agent_config and agent_config.get('name') == agent_identifier:
                    logger.debug(f"Found agent file by name match: {yaml_file}")
                    return yaml_file
                    
            except Exception as e:
                logger.warning(f"Error reading agent file {yaml_file}: {e}")
                continue
        
        logger.warning(f"Agent file not found for agent_identifier: {agent_identifier}")
        return None
    
    def _create_learning_entry(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a learning entry from the provided data.
        
        Args:
            data: Learning data from the event (contains learning nested object)
            
        Returns:
            Dict[str, Any]: Formatted learning entry
        """
        now = datetime.now().isoformat() + "Z"
        
        # Extract learning data from nested data.data structure
        # The 'data' parameter contains a data field with the actual learning data
        actual_data = data.get("data", {})
        learning_data = actual_data.get("learning", {})
        
        # Get learning content (required field)
        content = learning_data.get("content") or data.get("content", "Learning from agent interaction")
        learning_type = learning_data.get("type") or data.get("type", "agent_interaction")
        priority = learning_data.get("priority") or data.get("priority", "medium")
        context = learning_data.get("context") or data.get("context", "Agent interaction")
        tags = learning_data.get("tags") or data.get("tags", ["agent_learning", "interaction"])
        
        # Ensure priority is always a string
        if isinstance(priority, (int, float)):
            # Convert numeric priority to string equivalent
            priority_map = {5: "critical", 4: "high", 3: "medium", 2: "low", 1: "contextual"}
            priority = priority_map.get(int(priority), "medium")
        
        learning_entry = {
            "type": learning_type,
            "content": content,
            "priority": priority,
            "context": context,
            "tags": tags,
            "created_at": now,
            "updated_at": now,
            "usage_count": 0
        }
        
        logger.debug(f"Created learning entry: {learning_entry}")
        return learning_entry
    
    def _add_learning_to_yaml_file(self, agent_file: Path, learning_entry: Dict[str, Any]) -> bool:
        """Add learning entry to the agent's YAML file.
        
        Args:
            agent_file: Path to the agent YAML file
            learning_entry: Learning entry to add
            
        Returns:
            bool: True if successfully added, False otherwise
        """
        try:
            # Read existing agent configuration
            with open(agent_file, 'r', encoding='utf-8') as f:
                agent_config = yaml.safe_load(f) or {}
            
            # Initialize learning structure if it doesn't exist
            if 'learning' not in agent_config:
                agent_config['learning'] = []
            
            # Handle both list format and legacy dict format with 'items'
            if isinstance(agent_config['learning'], dict):
                # Legacy format with 'items' key
                if 'items' not in agent_config['learning']:
                    agent_config['learning']['items'] = []
                agent_config['learning']['items'].append(learning_entry)
            else:
                # New format - direct list
                agent_config['learning'].append(learning_entry)
            
            # Write back to file
            with open(agent_file, 'w', encoding='utf-8') as f:
                yaml.dump(agent_config, f, default_flow_style=False, allow_unicode=True, indent=2)
            
            logger.info(f"Successfully added learning entry to {agent_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding learning to YAML file {agent_file}: {e}")
            return False