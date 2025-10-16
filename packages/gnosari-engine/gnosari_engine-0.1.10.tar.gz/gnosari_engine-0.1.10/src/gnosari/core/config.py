"""
Configuration schemas and validation for Gnosari AI Teams.
"""

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, validator
import yaml
import os


class KnowledgeConfig(BaseModel):
    """Configuration for a knowledge base."""
    name: str
    type: str = Field(description="Type of knowledge base (website, documents, etc.)")
    data: List[str] = Field(description="Data sources for the knowledge base")
    config: Optional[Dict[str, Any]] = Field(default=None, description="Additional configuration")


class ToolConfig(BaseModel):
    """Configuration for a tool."""
    name: str
    module: Optional[str] = Field(default=None, description="Python module path")
    class_name: Optional[str] = Field(default=None, alias="class", description="Class name")
    url: Optional[str] = Field(default=None, description="MCP server URL")
    args: Optional[Dict[str, Any]] = Field(default=None, description="Tool arguments")
    
    @validator('module', 'class_name')
    def validate_tool_source(cls, v, values):
        """Ensure either module/class or url is provided."""
        if 'url' not in values and not v:
            raise ValueError("Either module/class or url must be provided")
        return v


class AgentConfig(BaseModel):
    """Configuration for an agent."""
    name: str
    instructions: str
    model: str = Field(default="gpt-4o", description="LLM model to use")
    temperature: float = Field(default=0.1, ge=0.0, le=2.0, description="Temperature for LLM")
    reasoning_effort: Optional[str] = Field(default=None, description="Reasoning effort level")
    orchestrator: bool = Field(default=False, description="Whether this is an orchestrator agent")
    tools: Optional[List[str]] = Field(default=None, description="List of tool names")
    knowledge: Optional[List[str]] = Field(default=None, description="List of knowledge base names")
    parallel_tool_calls: bool = Field(default=True, description="Enable parallel tool calls")
    can_transfer_to: Optional[List[str]] = Field(default=None, description="Agents this can transfer to")


class TeamConfig(BaseModel):
    """Configuration for a team."""
    name: str
    description: Optional[str] = Field(default=None, description="Team description")
    knowledge: Optional[List[KnowledgeConfig]] = Field(default=None, description="Knowledge bases")
    tools: Optional[List[ToolConfig]] = Field(default=None, description="Tools")
    agents: List[AgentConfig] = Field(description="List of agents")
    max_turns: Optional[int] = Field(default=None, description="Maximum turns for execution")
    
    @validator('agents')
    def validate_orchestrator(cls, v):
        """Ensure exactly one orchestrator exists."""
        orchestrators = [agent for agent in v if agent.orchestrator]
        if len(orchestrators) != 1:
            raise ValueError("Exactly one orchestrator agent is required")
        return v
    
    @classmethod
    def from_yaml(cls, file_path: str) -> 'TeamConfig':
        """Load team configuration from YAML file."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Configuration file not found: {file_path}")
        
        with open(file_path, 'r') as f:
            data = yaml.safe_load(f)
        
        return cls(**data)
    
    def to_yaml(self, file_path: str) -> None:
        """Save team configuration to YAML file."""
        data = self.dict(by_alias=True, exclude_none=True)
        
        with open(file_path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)