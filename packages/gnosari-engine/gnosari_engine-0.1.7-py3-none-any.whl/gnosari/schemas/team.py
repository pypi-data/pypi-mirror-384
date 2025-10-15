"""
Team-related schemas for Gnosari AI Teams.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, validator

from .base import BaseIOSchema
from .agent import AgentCreateRequest, AgentResponse
from .event import QueueConfig, EventConfig


class KnowledgeBaseConfig(BaseIOSchema):
    """Configuration for a knowledge base."""
    name: str = Field(description="Knowledge base name")
    type: str = Field(description="Type of knowledge base (website, documents, etc.)")
    data: List[str] = Field(description="Data sources for the knowledge base")
    config: Optional[Dict[str, Any]] = Field(default=None, description="Additional configuration")
    description: Optional[str] = Field(default=None, description="Knowledge base description")


class ToolConfig(BaseIOSchema):
    """Configuration for a tool."""
    name: str = Field(description="Tool name")
    module: Optional[str] = Field(default=None, description="Python module path")
    class_name: Optional[str] = Field(default=None, alias="class", description="Class name")
    url: Optional[str] = Field(default=None, description="MCP server URL")
    command: Optional[str] = Field(default=None, description="MCP server command")
    connection_type: Optional[str] = Field(default="sse", description="MCP connection type")
    args: Optional[Dict[str, Any]] = Field(default=None, description="Tool arguments")
    headers: Optional[Dict[str, str]] = Field(default=None, description="HTTP headers for MCP")
    timeout: Optional[int] = Field(default=30, description="Connection timeout")


class TeamCreateRequest(BaseIOSchema):
    """Request schema for creating a team."""
    name: str = Field(description="Team name")
    description: Optional[str] = Field(default=None, description="Team description")
    knowledge: Optional[List[KnowledgeBaseConfig]] = Field(default=None, description="Knowledge bases")
    tools: Optional[List[ToolConfig]] = Field(default=None, description="Tools configuration")
    agents: List[AgentCreateRequest] = Field(description="List of agents")
    max_turns: Optional[int] = Field(default=None, description="Maximum turns for execution")
    queues: Optional[List[QueueConfig]] = Field(default=None, description="Dynamic queue configurations")
    events: Optional[EventConfig] = Field(default=None, description="Event system configuration")
    
    @validator('agents')
    def validate_orchestrator(cls, v):
        """Ensure exactly one orchestrator exists."""
        orchestrators = [agent for agent in v if agent.orchestrator]
        if len(orchestrators) != 1:
            raise ValueError("Exactly one orchestrator agent is required")
        return v


class TeamResponse(BaseIOSchema):
    """Response schema for team operations."""
    id: str = Field(description="Team ID")
    name: str = Field(description="Team name") 
    description: Optional[str] = Field(description="Team description")
    orchestrator: AgentResponse = Field(description="Orchestrator agent")
    workers: List[AgentResponse] = Field(description="Worker agents")
    knowledge_bases: List[str] = Field(description="Available knowledge bases")
    tools: List[str] = Field(description="Available tools")
    max_turns: Optional[int] = Field(description="Maximum turns setting")
    status: str = Field(description="Team status")
    created_at: str = Field(description="Creation timestamp")


class TeamExecutionRequest(BaseIOSchema):
    """Request schema for executing a team."""
    message: str = Field(description="Initial message for the team")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Execution context")
    stream: bool = Field(default=False, description="Whether to stream responses")
    agent: Optional[str] = Field(default=None, description="Specific agent to run (optional)")
    max_turns: Optional[int] = Field(default=None, description="Override max turns")
    debug: bool = Field(default=False, description="Enable debug mode")


class TeamExecutionResponse(BaseIOSchema):
    """Response schema for team execution."""
    team_id: str = Field(description="Team ID")
    execution_id: str = Field(description="Execution ID")
    message: str = Field(description="Original message")
    response: str = Field(description="Final response")
    agent_interactions: List[Dict[str, Any]] = Field(description="Agent interaction history")
    usage: Optional[Dict[str, Any]] = Field(default=None, description="Total usage statistics")
    execution_time: float = Field(description="Total execution time in seconds")
    status: str = Field(description="Execution status")


class TeamStatus(BaseIOSchema):
    """Team status information."""
    team_id: str = Field(description="Team ID")
    name: str = Field(description="Team name")
    status: str = Field(description="Current status")
    orchestrator_status: str = Field(description="Orchestrator status")
    worker_statuses: Dict[str, str] = Field(description="Worker agent statuses")
    active_executions: int = Field(description="Number of active executions")
    last_activity: Optional[str] = Field(default=None, description="Last activity timestamp")


class TeamMetrics(BaseIOSchema):
    """Team performance metrics."""
    team_id: str = Field(description="Team ID")
    name: str = Field(description="Team name")
    total_executions: int = Field(description="Total executions")
    avg_execution_time: float = Field(description="Average execution time")
    success_rate: float = Field(description="Success rate percentage")
    agent_metrics: Dict[str, Dict[str, Any]] = Field(description="Per-agent metrics")
    knowledge_base_usage: Dict[str, int] = Field(description="Knowledge base usage counts")
    tool_usage: Dict[str, int] = Field(description="Tool usage counts")


class TeamConfigUpdate(BaseIOSchema):
    """Schema for updating team configuration."""
    name: Optional[str] = Field(default=None, description="Updated team name")
    description: Optional[str] = Field(default=None, description="Updated description")
    max_turns: Optional[int] = Field(default=None, description="Updated max turns")
    add_agents: Optional[List[AgentCreateRequest]] = Field(default=None, description="Agents to add")
    remove_agents: Optional[List[str]] = Field(default=None, description="Agent names to remove")
    add_knowledge: Optional[List[KnowledgeBaseConfig]] = Field(default=None, description="Knowledge bases to add")
    remove_knowledge: Optional[List[str]] = Field(default=None, description="Knowledge base names to remove")
    add_tools: Optional[List[ToolConfig]] = Field(default=None, description="Tools to add")
    remove_tools: Optional[List[str]] = Field(default=None, description="Tool names to remove")


class HandoffEvent(BaseIOSchema):
    """Schema for handoff events in team execution."""
    from_agent: str = Field(description="Source agent name")
    to_agent: str = Field(description="Target agent name")
    reason: str = Field(description="Handoff reason")
    message: str = Field(description="Handoff message")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Handoff context")
    timestamp: str = Field(description="Event timestamp")


class ExecutionEvent(BaseIOSchema):
    """Schema for execution events in team workflows."""
    event_type: str = Field(description="Event type (start, handoff, tool_call, end, error)")
    agent: str = Field(description="Agent involved in the event")
    message: Optional[str] = Field(default=None, description="Event message")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Event data")
    timestamp: str = Field(description="Event timestamp")
    execution_id: str = Field(description="Associated execution ID")