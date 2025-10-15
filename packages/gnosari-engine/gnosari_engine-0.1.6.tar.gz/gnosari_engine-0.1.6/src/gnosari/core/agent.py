"""
Base agent classes and interfaces for Gnosari AI Teams.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass


@dataclass
class AgentConfig:
    """Configuration for an agent."""
    name: str
    instructions: str
    model: str = "gpt-4o"
    temperature: float = 0.1
    reasoning_effort: Optional[str] = None
    orchestrator: bool = False
    tools: Optional[List[str]] = None
    knowledge: Optional[List[str]] = None
    parallel_tool_calls: bool = True
    can_transfer_to: Optional[List[str]] = None


class BaseAgent(ABC):
    """Base agent interface."""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.name = config.name
        
    @abstractmethod
    async def run(self, message: str, context: Optional[Dict[str, Any]] = None) -> Any:
        """Run the agent with a message."""
        pass
    
    @abstractmethod
    def add_tool(self, tool: Any) -> None:
        """Add a tool to the agent."""
        pass


class GnosariAgent(BaseAgent):
    """Gnosari-specific agent implementation using OpenAI Agents SDK."""
    
    def __init__(self, config: AgentConfig, openai_agent: Any = None):
        super().__init__(config)
        self.openai_agent = openai_agent
        self._tools = []
        
    async def run(self, message: str, context: Optional[Dict[str, Any]] = None) -> Any:
        """Run the agent using OpenAI Agents SDK."""
        if not self.openai_agent:
            raise ValueError("OpenAI agent not initialized")
        return await self.openai_agent.run(message)
    
    def add_tool(self, tool: Any) -> None:
        """Add a tool to the agent."""
        self._tools.append(tool)
        if self.openai_agent and hasattr(self.openai_agent, 'tools'):
            self.openai_agent.tools.append(tool)