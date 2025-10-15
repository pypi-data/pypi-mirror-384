"""Learning system schema definitions for the Gnosari framework."""

import json
from typing import Dict, List, Optional, Any, Literal
from pydantic import Field, field_validator
from .base import BaseIOSchema


# Specialized Learning Framework Schemas

class LearningCriterion(BaseIOSchema):
    """Individual analysis criterion configuration for learning strategies."""
    
    criterion: str = Field(..., description="Criterion identifier")
    description: str = Field(..., description="Human-readable criterion description")
    weight: float = Field(default=1.0, ge=0.1, le=2.0, description="Criterion importance weight (0.1-2.0)")


class LearningStrategyConfig(BaseIOSchema):
    """Learning strategy component configuration schema."""
    
    id: str = Field(..., description="Strategy identifier (auto-inferred from filename)")
    name: str = Field(..., description="Human-readable strategy name")
    description: str = Field(..., description="Strategy description")
    category: str = Field(..., description="Strategy category (e.g., 'organizational', 'technical')")
    tags: List[str] = Field(default_factory=list, description="Strategy tags for categorization")
    focus_areas: List[str] = Field(..., description="Learning focus areas")
    analysis_criteria: List[LearningCriterion] = Field(..., description="Analysis criteria with weights")
    learning_objectives: List[str] = Field(..., description="Learning objectives")
    instruction_templates: Optional[Dict[str, str]] = Field(default=None, description="Instruction templates for prompts")


class SuccessMetric(BaseIOSchema):
    """Success metric definition for competency assessment."""
    
    metric: str = Field(..., description="Metric identifier")
    target: float = Field(..., ge=0.0, le=1.0, description="Target value (0.0-1.0)")
    description: str = Field(..., description="Metric description")


class CompetencyConfig(BaseIOSchema):
    """Competency focus component configuration schema."""
    
    id: str = Field(..., description="Competency identifier (auto-inferred from filename)")
    name: str = Field(..., description="Human-readable competency name")
    description: str = Field(..., description="Competency description")
    category: str = Field(..., description="Competency category")
    assessment_criteria: List[str] = Field(..., description="Assessment criteria list")
    success_metrics: Optional[List[SuccessMetric]] = Field(default=None, description="Success metrics")
    improvement_indicators: Optional[List[str]] = Field(default=None, description="Improvement indicators")


class LearningPriority(BaseIOSchema):
    """Learning priority definition for agent-specific focus."""
    
    level: Literal["critical", "high", "medium", "low"] = Field(..., description="Priority level")
    content: str = Field(..., description="Priority content description")
    context: str = Field(..., description="Context where priority applies")


class AgentLearningConfig(BaseIOSchema):
    """Agent-level learning configuration schema."""
    
    learning_strategy: Optional[str] = Field(default=None, description="Learning strategy ID reference")
    competency_focus: List[str] = Field(default_factory=list, description="Competency focus ID references")
    learning_priorities: List[LearningPriority] = Field(default_factory=list, description="Agent-specific learning priorities")


class TeamLearningConfig(BaseIOSchema):
    """Team-level learning configuration schema."""
    
    enabled: bool = Field(default=True, description="Enable learning for this team")
    learning_agent: str = Field(description="Name of the agent to use for learning")
    default_strategy: Optional[str] = Field(default=None, description="Default learning strategy for agents")
    session_limit: Optional[int] = Field(default=100, description="Max sessions to analyze")
    execution_mode: Literal["sync", "async"] = Field(default="async", description="Learning execution mode")


class LearningConfig(BaseIOSchema):
    """Configuration schema for team learning."""
    
    enabled: bool = Field(default=True, description="Enable learning for this team")
    learning_agent: str = Field(description="Name of the agent to use for learning")
    session_limit: Optional[int] = Field(default=100, description="Max sessions to analyze")
    execution_mode: Literal["sync", "async"] = Field(default="async", description="Learning execution mode")
    learning_frequency: Optional[str] = Field(default="manual", description="Learning frequency")
    queue_name: Optional[str] = Field(default="learning_queue", description="Queue name for async processing")
    memory_provider: Optional[Literal["yaml", "database"]] = Field(default="yaml", description="Memory storage provider (yaml or database)")
    memory_database_url: Optional[str] = Field(default=None, description="Database URL for database memory provider")
    backup_enabled: bool = Field(default=True, description="Enable backups for YAML memory provider")
    
    @field_validator('learning_agent')
    @classmethod
    def validate_learning_agent(cls, v):
        """Validate learning agent name is not empty."""
        if not v or not v.strip():
            raise ValueError('Learning agent name cannot be empty')
        return v.strip()


class LearningRequest(BaseIOSchema):
    """Request schema for learning processing."""
    
    team_path: str = Field(description="Path to team configuration")
    target_agents: Optional[List[str]] = Field(default=None, description="Specific agents to learn")
    session_context: Optional[Dict[str, Any]] = Field(default=None, description="Session context for filtering")
    execution_mode: Optional[Literal["sync", "async"]] = Field(default="async", description="Override execution mode")
    team_wide_learning: bool = Field(default=False, description="Use all team conversations for learning, not just agent-specific sessions")
    
    @field_validator('team_path')
    @classmethod
    def validate_team_path(cls, v):
        """Validate team path is not empty."""
        if not v or not v.strip():
            raise ValueError('Team path cannot be empty')
        return v.strip()


class LearningResponse(BaseIOSchema):
    """Response schema for learning results."""
    
    agent_name: str = Field(description="Agent that was learned")
    original_memory: Optional[str] = Field(default=None, description="Original agent memory")
    updated_memory: Optional[str] = Field(default=None, description="Updated agent memory")
    has_changes: bool = Field(description="Whether any memory changes were made")
    learning_summary: str = Field(description="Summary of memory changes made")
    confidence_score: Optional[float] = Field(default=None, description="Confidence in the learning")
    
    # Deprecated fields for backward compatibility
    original_instructions: str = Field(default="", description="[DEPRECATED] Original agent instructions")
    updated_instructions: str = Field(default="", description="[DEPRECATED] Updated agent instructions")
    
    @field_validator('updated_memory')
    @classmethod
    def validate_learning_response(cls, v, info):
        """Validate learning agent memory response format."""
        # Empty/None/empty string means no changes
        if v is None or v == "" or (isinstance(v, str) and v.strip() == ""):
            if hasattr(info, 'data') and info.data:
                info.data['has_changes'] = False
            return v
        
        # Non-empty string means memory updates
        if v and isinstance(v, str):
            if hasattr(info, 'data') and info.data:
                info.data['has_changes'] = True
            return v
        
        raise ValueError("Learning response must be either None/empty string or memory string")


class SessionContext(BaseIOSchema):
    """Context schema for session filtering and retrieval."""
    
    team_identifier: str = Field(description="Team identifier for session filtering")
    agent_names: List[str] = Field(description="List of agent names to retrieve sessions for")
    time_range: Optional[Dict[str, str]] = Field(default=None, description="Time range filter (start/end dates)")
    session_types: Optional[List[str]] = Field(default=None, description="Types of sessions to include")
    max_sessions: Optional[int] = Field(default=100, description="Maximum number of sessions to retrieve")


class LearningContext(BaseIOSchema):
    """Extended context for learning operations."""
    
    team_identifier: str = Field(description="Team identifier")
    agent_names: List[str] = Field(description="List of agent names")
    session_filters: Dict[str, Any] = Field(description="Session filtering criteria")
    learning_config: LearningConfig = Field(description="Learning configuration")
    session_count: Optional[int] = Field(default=None, description="Number of sessions found")
    time_period: Optional[str] = Field(default=None, description="Time period of analysis")
    execution_mode: str = Field(default="manual", description="Learning execution mode")
    team_path: Optional[str] = Field(default=None, description="Path to team configuration for learning specialization")


class LearningTaskStatus(BaseIOSchema):
    """Status schema for learning tasks."""
    
    task_id: str = Field(description="Unique task identifier")
    status: Literal["pending", "processing", "completed", "failed"] = Field(description="Current task status")
    agent_name: str = Field(description="Agent being processed")
    team_path: str = Field(description="Team configuration path")
    created_at: str = Field(description="Task creation timestamp")
    updated_at: str = Field(description="Last update timestamp")
    error_message: Optional[str] = Field(default=None, description="Error message if task failed")
    result: Optional[LearningResponse] = Field(default=None, description="Learning result if completed")


class LearningError(Exception):
    """Custom exception for learning system errors."""
    
    def __init__(self, message: str, error_code: str = None, agent_name: str = None):
        """Initialize learning error.
        
        Args:
            message: Error message
            error_code: Optional error code for categorization
            agent_name: Optional agent name where error occurred
        """
        self.message = message
        self.error_code = error_code
        self.agent_name = agent_name
        super().__init__(self.message)


# Input/Output schemas for learning tool
class LearningToolInput(BaseIOSchema):
    """Input schema for learning tool operations."""
    
    team_path: str = Field(description="Path to team configuration file or directory")
    agent_name: Optional[str] = Field(default=None, description="Specific agent to learn (optional)")
    execution_mode: Literal["sync", "async"] = Field(default="async", description="Learning execution mode")
    wait_for_completion: bool = Field(default=False, description="Wait for async learning to complete")


class LearningToolOutput(BaseIOSchema):
    """Output schema for learning tool operations."""
    
    success: bool = Field(description="Whether the learning operation succeeded")
    message: str = Field(description="Result message")
    task_ids: Optional[List[str]] = Field(default=None, description="Task IDs for async operations")
    results: Optional[List[LearningResponse]] = Field(default=None, description="Learning results for sync operations")
    error_details: Optional[Dict[str, Any]] = Field(default=None, description="Error details if operation failed")