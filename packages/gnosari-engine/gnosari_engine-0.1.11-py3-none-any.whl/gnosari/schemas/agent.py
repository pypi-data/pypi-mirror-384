"""
Agent-related schemas for Gnosari AI Teams.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, validator
from enum import Enum

from .base import BaseIOSchema
from .trait import TraitConfig
from .event import AgentListener, AgentTrigger


class LearningType(str, Enum):
    """Learning types for agent learnings."""
    HOWTO = "howto"
    BEST_PRACTICES = "best_practices"
    WARNINGS = "warnings"
    CONTEXT_MEMORY = "context_memory"
    PATTERNS = "patterns"
    EMOTIONAL_INTELLIGENCE = "emotional_intelligence"
    COMMUNICATION_STYLE = "communication_style"
    DOMAIN_EXPERTISE = "domain_expertise"
    WORKFLOW_OPTIMIZATION = "workflow_optimization"
    ERROR_RECOVERY = "error_recovery"
    USER_PREFERENCES = "user_preferences"
    CREATIVE_SOLUTIONS = "creative_solutions"
    COLLABORATION_INSIGHTS = "collaboration_insights"
    EFFICIENCY_HACKS = "efficiency_hacks"
    CULTURAL_AWARENESS = "cultural_awareness"
    ADAPTIVE_REASONING = "adaptive_reasoning"
    INNOVATION_PATTERNS = "innovation_patterns"


class LearningPriority(str, Enum):
    """Priority levels for learning application."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    CONTEXTUAL = "contextual"


class LearningObjective(BaseIOSchema):
    """Configuration schema for learning objectives."""
    id: Optional[str] = Field(default=None, description="Optional ID for the learning objective")
    objective: str = Field(description="The learning objective description")
    
    @validator('objective')
    def validate_objective_length(cls, v):
        if len(v.strip()) < 5:
            raise ValueError('Learning objective must be at least 5 characters')
        if len(v) > 500:
            raise ValueError('Learning objective must be less than 500 characters')
        return v.strip()


class LearningConfig(BaseIOSchema):
    """Configuration schema for agent learnings."""
    type: LearningType = Field(description="Type of learning")
    content: str = Field(description="Learning content/description")
    priority: LearningPriority = Field(default=LearningPriority.MEDIUM, description="Learning priority")
    context: Optional[str] = Field(default=None, description="When this learning applies")
    tags: Optional[List[str]] = Field(default=None, description="Tags for categorization")
    created_at: Optional[str] = Field(default=None, description="Creation timestamp")
    updated_at: Optional[str] = Field(default=None, description="Last update timestamp")
    usage_count: int = Field(default=0, description="How often this learning was referenced")
    
    @validator('content')
    def validate_content_length(cls, v):
        if len(v.strip()) < 10:
            raise ValueError('Learning content must be at least 10 characters')
        if len(v) > 2000:
            raise ValueError('Learning content must be less than 2000 characters')
        return v.strip()


class AgentCreateRequest(BaseIOSchema):
    """Request schema for creating an agent."""
    name: str = Field(description="Agent name")
    instructions: str = Field(description="Agent instructions")
    model: str = Field(default="gpt-4o", description="LLM model to use")
    temperature: float = Field(default=0.1, ge=0.0, le=2.0, description="Temperature for LLM")
    reasoning_effort: Optional[str] = Field(default=None, description="Reasoning effort level")
    orchestrator: bool = Field(default=False, description="Whether this is an orchestrator agent")
    tools: Optional[List[str]] = Field(default=None, description="List of tool names")
    knowledge: Optional[List[str]] = Field(default=None, description="List of knowledge base names")
    parallel_tool_calls: bool = Field(default=True, description="Enable parallel tool calls")
    can_transfer_to: Optional[List[str]] = Field(default=None, description="Agents this can transfer to")
    traits: Optional[List[TraitConfig]] = Field(default=None, description="Personality traits for the agent")
    learning: Optional[List[LearningConfig]] = Field(default=None, description="Agent learnings from experience")
    learning_objectives: Optional[List[LearningObjective]] = Field(default=None, description="Learning objectives for the agent")
    listen: Optional[AgentListener] = Field(default=None, description="Event listener configuration for this agent")
    trigger: Optional[List[AgentTrigger]] = Field(default=None, description="Event trigger configurations for this agent")
    
    @validator('traits')
    def validate_traits(cls, v):
        """Validate trait configuration."""
        if v is None:
            return v
        
        # Maximum 5 traits per agent
        if len(v) > 5:
            raise ValueError('Maximum 5 traits allowed per agent')
        
        # Validate trait names are unique
        names = [trait.name for trait in v]
        if len(names) != len(set(names)):
            raise ValueError('Trait names must be unique within an agent')
        
        return v


class AgentResponse(BaseIOSchema):
    """Response schema for agent operations."""
    id: str = Field(description="Agent ID")
    name: str = Field(description="Agent name")
    instructions: str = Field(description="Agent instructions")
    model: str = Field(description="LLM model being used")
    temperature: float = Field(description="Temperature setting")
    orchestrator: bool = Field(description="Whether this is an orchestrator agent")
    tools: List[str] = Field(description="List of available tools")
    knowledge: List[str] = Field(description="List of knowledge bases")
    status: str = Field(description="Agent status")
    created_at: str = Field(description="Creation timestamp")


class AgentExecutionRequest(BaseIOSchema):
    """Request schema for executing an agent."""
    message: str = Field(description="Message to send to the agent")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Optional execution context")
    stream: bool = Field(default=False, description="Whether to stream the response")
    max_turns: Optional[int] = Field(default=None, description="Maximum number of turns")


class AgentExecutionResponse(BaseIOSchema):
    """Response schema for agent execution."""
    agent_id: str = Field(description="Agent ID")
    message: str = Field(description="Original message")
    response: str = Field(description="Agent response")
    usage: Optional[Dict[str, Any]] = Field(default=None, description="Token usage information")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")
    execution_time: float = Field(description="Execution time in seconds")


class AgentHandoffRequest(BaseIOSchema):
    """Request schema for agent handoffs."""
    from_agent: str = Field(description="Source agent name")
    to_agent: str = Field(description="Target agent name")
    message: str = Field(description="Message to handoff")
    reason: str = Field(description="Reason for handoff")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Handoff context")


class AgentStatus(BaseIOSchema):
    """Agent status information."""
    name: str = Field(description="Agent name")
    status: str = Field(description="Current status")
    last_activity: Optional[str] = Field(default=None, description="Last activity timestamp")
    current_task: Optional[str] = Field(default=None, description="Current task description")
    tools_available: List[str] = Field(description="Available tools")
    knowledge_bases: List[str] = Field(description="Available knowledge bases")


class AgentMetrics(BaseIOSchema):
    """Agent performance metrics."""
    agent_name: str = Field(description="Agent name")
    total_executions: int = Field(description="Total number of executions")
    avg_execution_time: float = Field(description="Average execution time in seconds")
    total_tokens_used: int = Field(description="Total tokens consumed")
    success_rate: float = Field(description="Success rate percentage")
    last_24h_executions: int = Field(description="Executions in last 24 hours")
    error_count: int = Field(description="Total number of errors")


class AgentConfigUpdate(BaseIOSchema):
    """Schema for updating agent configuration."""
    instructions: Optional[str] = Field(default=None, description="Updated instructions")
    model: Optional[str] = Field(default=None, description="Updated model")
    temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0, description="Updated temperature")
    tools: Optional[List[str]] = Field(default=None, description="Updated tool list")
    knowledge: Optional[List[str]] = Field(default=None, description="Updated knowledge base list")
    can_transfer_to: Optional[List[str]] = Field(default=None, description="Updated transfer targets")