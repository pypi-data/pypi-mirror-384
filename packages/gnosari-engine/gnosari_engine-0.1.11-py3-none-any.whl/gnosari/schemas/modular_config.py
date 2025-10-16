"""
Modular configuration schemas for Gnosari AI Teams.

This module provides Pydantic schemas for the modular team configuration system,
supporting directory-based component organization with type inference.
"""
from typing import Optional, List, Dict, Any, Union
from pydantic import Field, validator
from .base import BaseIOSchema
from .trait import TraitConfig
from .agent import LearningConfig
from .utils import create_identifier_validator


class TraitReference(BaseIOSchema):
    """Reference to a trait component with optional weight override."""
    name: str = Field(description="Trait component identifier (filename without extension)")
    weight: Optional[float] = Field(None, ge=0.0, le=2.0, description="Override weight for this trait")
    
    # Normalize trait reference to match filename-based identifiers
    _validate_name = validator('name', allow_reuse=True)(create_identifier_validator('trait reference name'))


class ComponentConfig(BaseIOSchema):
    """Base configuration for modular components with required ID field."""
    id: str = Field(description="Component identifier (typically inferred from filename)")


class AgentComponentConfig(ComponentConfig):
    """Agent component configuration (agents/ directory)."""
    name: Optional[str] = Field(None, description="Display name for the agent")
    description: Optional[str] = Field(None, description="Agent description")
    instructions: str = Field(description="Agent instructions/prompt")
    model: Optional[str] = Field("gpt-4o", description="LLM model")
    temperature: Optional[float] = Field(0.7, description="Model temperature")
    reasoning_effort: Optional[str] = Field("medium", description="Reasoning effort level")
    orchestrator: Optional[bool] = Field(False, description="Is orchestrator agent")
    tools: Optional[List[str]] = Field(default_factory=list, description="Tool component references")
    knowledge: Optional[List[str]] = Field(default_factory=list, description="Knowledge component references")
    traits: Optional[List[Union[str, TraitReference]]] = Field(default_factory=list, description="Trait component references with optional weight overrides")
    delegation: Optional[List[Dict[str, str]]] = Field(default_factory=list, description="Delegation configuration")
    learning: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="Agent learnings from experience")
    learning_objectives: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="Learning objectives for the agent")
    memory: Optional[str] = Field(default="", description="Agent memory from previous interactions")
    listen: Optional[Union[List[str], List[Dict[str, Any]]]] = Field(default_factory=list, description="Event listener configuration - simple list of event types or list of event objects with specific instructions")
    trigger: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="Event trigger configuration for publishing events")

    @validator('temperature')
    def validate_temperature(cls, v):
        if v is not None and (v < 0 or v > 2):
            raise ValueError('Temperature must be between 0 and 2')
        return v

    @validator('reasoning_effort')
    def validate_reasoning_effort(cls, v):
        if v is not None and v not in ['low', 'medium', 'high']:
            raise ValueError('Reasoning effort must be one of: low, medium, high')
        return v


class ToolComponentConfig(ComponentConfig):
    """Tool component configuration (tools/ directory)."""
    name: Optional[str] = Field(None, description="Display name for the tool")
    description: Optional[str] = Field(None, description="Tool description")
    module: Optional[str] = Field(None, description="Python module path for built-in tools")
    class_name: Optional[str] = Field(None, description="Tool class name")
    url: Optional[str] = Field(None, description="MCP server URL")
    command: Optional[str] = Field(None, description="MCP server command")
    connection_type: Optional[str] = Field(None, description="MCP connection type")
    args: Optional[Union[Dict[str, Any], List[str]]] = Field(default_factory=dict, description="Tool arguments (dict for built-in tools, list for MCP server commands)")
    headers: Optional[Dict[str, str]] = Field(default_factory=dict, description="HTTP headers for MCP")
    timeout: Optional[int] = Field(None, description="Connection timeout")

    @validator('timeout')
    def validate_timeout(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Timeout must be positive')
        return v


class KnowledgeComponentConfig(ComponentConfig):
    """Knowledge component configuration (knowledge/ directory)."""
    name: Optional[str] = Field(None, description="Display name for the knowledge base")
    description: Optional[str] = Field(None, description="Knowledge base description")
    type: str = Field(description="Knowledge type: website|sitemap|youtube|pdf|text|csv|json|directory")
    data: List[str] = Field(description="Data sources array")
    config: Optional[Dict[str, Any]] = Field(None, description="Embedchain configuration")

    @validator('type')
    def validate_type(cls, v):
        valid_types = ['website', 'sitemap', 'youtube', 'pdf', 'text', 'csv', 'json', 'directory']
        if v not in valid_types:
            raise ValueError(f'Knowledge type must be one of: {", ".join(valid_types)}')
        return v

    @validator('data')
    def validate_data(cls, v):
        if not v:
            raise ValueError('Data sources cannot be empty')
        return v


class PromptComponentConfig(ComponentConfig):
    """Prompt component configuration (prompts/ directory)."""
    template: Optional[str] = Field(None, description="Prompt template content")
    content: Optional[str] = Field(None, description="Direct prompt content")
    instructions: Optional[str] = Field(None, description="Instruction-based prompt")
    variables: Optional[Dict[str, str]] = Field(default_factory=dict, description="Template variables")

    @validator('template', 'content', 'instructions', always=True)
    def validate_at_least_one_content(cls, v, values):
        template = values.get('template')
        content = values.get('content')
        instructions = values.get('instructions')
        
        if not any([template, content, instructions]):
            raise ValueError('Prompt component must have at least one of: template, content, or instructions')
        return v


class TraitComponentConfig(ComponentConfig):
    """Trait component configuration (traits/ directory)."""
    name: str = Field(description="Trait display name (e.g., 'Helpful', 'Professional', 'Analytical')")
    description: Optional[str] = Field(None, description="Human-readable trait description")
    instructions: str = Field(description="Specific instructions for this trait behavior")
    weight: float = Field(default=1.0, ge=0.0, le=2.0, description="Default trait influence weight")
    category: Optional[str] = Field(None, description="Trait category (e.g., 'personality', 'communication', 'workflow')")
    tags: Optional[List[str]] = Field(default_factory=list, description="Tags for trait organization")

    @validator('name')
    def validate_name(cls, v):
        """Ensure trait name is not empty."""
        if not v.strip():
            raise ValueError('Trait name cannot be empty')
        return v.strip()
    
    @validator('instructions')
    def validate_instructions(cls, v):
        """Ensure instructions are not empty and reasonable length."""
        if not v.strip():
            raise ValueError('Trait instructions cannot be empty')
        if len(v) > 1000:
            raise ValueError('Trait instructions must be under 1000 characters')
        return v.strip()
    
    @validator('instructions')
    def validate_safe_instructions(cls, v):
        """Ensure trait instructions are safe and appropriate."""
        dangerous_patterns = [
            'ignore previous instructions',
            'system prompt',
            'act as if',
            'pretend you are',
            'forget everything'
        ]
        
        v_lower = v.lower()
        for pattern in dangerous_patterns:
            if pattern in v_lower:
                raise ValueError(f'Trait instructions contain potentially unsafe content: {pattern}')
        
        return v


class TeamMainConfig(BaseIOSchema):
    """Main team configuration with hierarchical overrides."""
    name: str = Field(description="Team name")
    id: Optional[str] = Field(None, description="Team identifier")
    description: Optional[str] = Field(None, description="Team description")
    version: Optional[str] = Field("1.0.0", description="Configuration version")
    tags: Optional[List[str]] = Field(default_factory=list, description="Team tags")
    
    config: Optional[Dict[str, Any]] = Field(None, description="Team-level configuration")
    
    overrides: Optional[Dict[str, Dict[str, Dict[str, Any]]]] = Field(
        default_factory=dict, 
        description="Hierarchical component overrides"
    )
    
    components: Optional[Dict[str, Dict[str, List[str]]]] = Field(
        default_factory=dict,
        description="Component inclusion/exclusion filters with include/exclude keys"
    )

    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Team name cannot be empty')
        return v.strip()

    @validator('version')
    def validate_version(cls, v):
        if v and not v.replace('.', '').replace('-', '').replace('+', '').isalnum():
            raise ValueError('Version must be a valid semantic version')
        return v


class ModularTeamConfig(BaseIOSchema):
    """Complete modular team configuration after loading and composition."""
    main: TeamMainConfig = Field(description="Main team configuration")
    agents: Dict[str, AgentComponentConfig] = Field(default_factory=dict, description="Agent components")
    tools: Dict[str, ToolComponentConfig] = Field(default_factory=dict, description="Tool components") 
    knowledge: Dict[str, KnowledgeComponentConfig] = Field(default_factory=dict, description="Knowledge components")
    prompts: Dict[str, PromptComponentConfig] = Field(default_factory=dict, description="Prompt components")
    traits: Dict[str, TraitComponentConfig] = Field(default_factory=dict, description="Trait components")

    @validator('agents')
    def validate_agents(cls, v):
        if not v:
            raise ValueError('Team must have at least one agent')
        return v

    @validator('agents')
    def validate_orchestrator_exists(cls, v):
        orchestrators = [agent for agent in v.values() if agent.orchestrator]
        if not orchestrators:
            raise ValueError('Team must have at least one orchestrator agent')
        return v