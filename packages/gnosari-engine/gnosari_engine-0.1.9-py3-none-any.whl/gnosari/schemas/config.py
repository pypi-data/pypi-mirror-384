"""
Configuration-related schemas for Gnosari AI Teams.
"""

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, validator
from enum import Enum

from .base import BaseIOSchema


class LogLevel(str, Enum):
    """Logging levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ProviderType(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    DEEPSEEK = "deepseek"
    GOOGLE = "google"
    AZURE = "azure"


class ConnectionType(str, Enum):
    """MCP connection types."""
    SSE = "sse"
    STREAMABLE_HTTP = "streamable_http"
    STDIO = "stdio"


class GlobalConfig(BaseIOSchema):
    """Global configuration for Gnosari."""
    log_level: LogLevel = Field(default=LogLevel.INFO, description="Global logging level")
    debug: bool = Field(default=False, description="Enable debug mode")
    max_concurrent_executions: int = Field(default=10, description="Maximum concurrent executions")
    default_timeout: int = Field(default=300, description="Default timeout in seconds")
    enable_metrics: bool = Field(default=True, description="Enable metrics collection")
    metrics_retention_days: int = Field(default=30, description="Days to retain metrics")
    cache_enabled: bool = Field(default=True, description="Enable caching")
    cache_ttl: int = Field(default=3600, description="Cache TTL in seconds")


class ProviderConfig(BaseIOSchema):
    """Configuration for LLM providers."""
    provider: ProviderType = Field(description="Provider type")
    api_key: Optional[str] = Field(default=None, description="API key")
    base_url: Optional[str] = Field(default=None, description="Custom base URL")
    model: str = Field(description="Model name")
    temperature: float = Field(default=0.1, ge=0.0, le=2.0, description="Temperature")
    max_tokens: Optional[int] = Field(default=None, description="Maximum tokens")
    timeout: int = Field(default=300, description="Request timeout")
    additional_params: Optional[Dict[str, Any]] = Field(default=None, description="Additional parameters")


class KnowledgeConfig(BaseIOSchema):
    """Configuration for knowledge bases."""
    name: str = Field(description="Knowledge base name")
    type: str = Field(description="Knowledge base type")
    data_sources: List[str] = Field(description="Data sources")
    description: Optional[str] = Field(default=None, description="Description")
    embedchain_config: Optional[Dict[str, Any]] = Field(default=None, description="Embedchain configuration")
    refresh_interval: Optional[int] = Field(default=None, description="Refresh interval in seconds")
    max_documents: Optional[int] = Field(default=None, description="Maximum number of documents")


class ToolConfigSchema(BaseIOSchema):
    """Configuration schema for tools."""
    name: str = Field(description="Tool name")
    enabled: bool = Field(default=True, description="Whether tool is enabled")
    module: Optional[str] = Field(default=None, description="Python module")
    class_name: Optional[str] = Field(default=None, description="Class name")
    url: Optional[str] = Field(default=None, description="MCP server URL")
    command: Optional[str] = Field(default=None, description="MCP command")
    connection_type: ConnectionType = Field(default=ConnectionType.SSE, description="Connection type")
    args: Optional[Dict[str, Any]] = Field(default=None, description="Tool arguments")
    timeout: int = Field(default=30, description="Tool timeout")
    rate_limit: Optional[int] = Field(default=None, description="Rate limit per minute")


class AgentConfigSchema(BaseIOSchema):
    """Configuration schema for agents."""
    name: str = Field(description="Agent name")
    instructions: str = Field(description="Agent instructions")
    provider_config: ProviderConfig = Field(description="LLM provider configuration")
    orchestrator: bool = Field(default=False, description="Is orchestrator agent")
    tools: List[str] = Field(default_factory=list, description="Available tools")
    knowledge_bases: List[str] = Field(default_factory=list, description="Available knowledge bases")
    parallel_tool_calls: bool = Field(default=True, description="Enable parallel tool calls")
    can_transfer_to: List[str] = Field(default_factory=list, description="Transfer targets")
    max_turns: Optional[int] = Field(default=None, description="Maximum turns per conversation")
    reasoning_effort: Optional[str] = Field(default=None, description="Reasoning effort level")
    memory: Optional[str] = Field(default="", description="Agent memory from previous interactions")
    learning_objectives: Optional[List[Dict[str, Any]]] = Field(default=None, description="Learning objectives for the agent")


class TeamConfigSchema(BaseIOSchema):
    """Complete team configuration schema."""
    metadata: Dict[str, Any] = Field(description="Team metadata")
    global_config: GlobalConfig = Field(description="Global configuration")
    knowledge_bases: List[KnowledgeConfig] = Field(default_factory=list, description="Knowledge bases")
    tools: List[ToolConfigSchema] = Field(default_factory=list, description="Tools configuration")
    agents: List[AgentConfigSchema] = Field(description="Agents configuration")
    workflows: Optional[Dict[str, Any]] = Field(default=None, description="Workflow definitions")
    
    @validator('agents')
    def validate_orchestrator(cls, v):
        """Ensure exactly one orchestrator exists."""
        orchestrators = [agent for agent in v if agent.orchestrator]
        if len(orchestrators) != 1:
            raise ValueError("Exactly one orchestrator agent is required")
        return v
    
    @validator('agents')
    def validate_transfer_targets(cls, v):
        """Validate that transfer targets exist."""
        agent_names = {agent.name for agent in v}
        for agent in v:
            for target in agent.can_transfer_to:
                if target not in agent_names:
                    raise ValueError(f"Agent '{agent.name}' has invalid transfer target '{target}'")
        return v


class ConfigValidationResult(BaseIOSchema):
    """Result of configuration validation."""
    is_valid: bool = Field(description="Whether configuration is valid")
    errors: List[str] = Field(default_factory=list, description="Validation errors")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")
    suggestions: List[str] = Field(default_factory=list, description="Improvement suggestions")


class ConfigUpdateRequest(BaseIOSchema):
    """Request to update configuration."""
    section: str = Field(description="Configuration section to update")
    updates: Dict[str, Any] = Field(description="Updates to apply")
    validate_only: bool = Field(default=False, description="Only validate, don't apply")


class ConfigBackup(BaseIOSchema):
    """Configuration backup schema."""
    backup_id: str = Field(description="Backup identifier")
    timestamp: str = Field(description="Backup timestamp")
    config: TeamConfigSchema = Field(description="Backed up configuration")
    description: Optional[str] = Field(default=None, description="Backup description")


class ConfigMigration(BaseIOSchema):
    """Configuration migration information."""
    from_version: str = Field(description="Source configuration version")
    to_version: str = Field(description="Target configuration version")
    migration_steps: List[str] = Field(description="Migration steps performed")
    backup_created: bool = Field(description="Whether backup was created")
    success: bool = Field(description="Whether migration succeeded")
    errors: List[str] = Field(default_factory=list, description="Migration errors")