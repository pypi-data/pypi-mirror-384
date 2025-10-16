"""
Team Models - Shared models for team management using OpenAI Agents SDK integration.
"""

from typing import Dict, List, Optional, Any
from agents import Agent


class Team:
    """Team object containing orchestrator and worker agents using OpenAI Agents SDK."""
    
    def __init__(self, orchestrator: Agent, workers: Dict[str, Agent], name: Optional[str] = None, max_turns: Optional[int] = None, agent_id_to_name: Optional[Dict[str, str]] = None, original_config: Optional[Dict[str, Any]] = None):
        """Initialize the team.
        
        Args:
            orchestrator: The orchestrator/leader agent using OpenAI Agents SDK
            workers: Dictionary of worker agents using OpenAI Agents SDK
            name: Optional team name
            max_turns: Optional maximum turns for team execution
            agent_id_to_name: Optional mapping from agent IDs to agent names
            original_config: Original YAML configuration used to build this team
        """
        self.orchestrator = orchestrator
        self.workers = workers
        self.name = name
        self.max_turns = max_turns
        self.all_agents = {**workers, orchestrator.name: orchestrator}
        self.agent_id_to_name = agent_id_to_name or {}
        self.original_config = original_config
        
        # Create reverse mapping: name -> id
        self.name_to_agent_id = {name: agent_id for agent_id, name in self.agent_id_to_name.items()}

    def get_agent(self, name_or_id: str) -> Optional[Agent]:
        """Get an agent by name or ID.
        
        Args:
            name_or_id: Agent name or ID
            
        Returns:
            Agent instance or None if not found
        """
        # First try direct name lookup
        if name_or_id in self.all_agents:
            return self.all_agents.get(name_or_id)
        
        # If not found, try ID lookup
        if name_or_id in self.agent_id_to_name:
            agent_name = self.agent_id_to_name[name_or_id]
            return self.all_agents.get(agent_name)
        
        return None
    
    def list_agents(self) -> List[str]:
        """List all agent names and IDs in the team.
        
        Returns:
            List of agent names and IDs
        """
        agent_list = list(self.all_agents.keys())
        # Add IDs to the list for better error messages
        agent_list.extend(self.agent_id_to_name.keys())
        return agent_list