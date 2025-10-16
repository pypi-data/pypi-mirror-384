"""Session context schema for tools and runners."""

from typing import Optional, Dict, Any
from pydantic import Field
from .base import BaseIOSchema


class SessionContext(BaseIOSchema):
    """Session execution context for tools and runners - replaces TeamContext."""
    
    account_id: Optional[int] = Field(
        default=None, 
        description="Account identifier for multi-tenant scenarios"
    )
    
    # Integer IDs for database references (python-api style)
    team_id: Optional[int] = Field(
        default=None,
        description="Integer team ID (references teams table)"
    )
    
    agent_id: Optional[int] = Field(
        default=None,
        description="Integer agent ID (references agents table)"
    )
    
    # String identifiers from YAML configuration
    team_identifier: Optional[str] = Field(
        default=None,
        description="Team identifier from YAML root 'id' field"
    )
    
    agent_identifier: Optional[str] = Field(
        default=None,
        description="Agent identifier from YAML agents[].id field"
    )
    
    session_id: Optional[str] = Field(
        default=None,
        description="Session identifier for conversation tracking"
    )
    
    # Original YAML configuration for OpenAI Agents SDK compatibility
    original_config: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Original team configuration from YAML"
    )
    
    # For OpenAI Agents SDK compatibility - returns self as dict
    @property
    def session_context(self) -> Dict[str, Any]:
        """Get session context as dict for OpenAI Agents SDK compatibility."""
        return self.model_dump(exclude_none=True)
    
    # Extensibility for future context fields
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Additional context metadata"
    )


__all__ = [
    "SessionContext"
]