"""Trait schema definitions for agent personality and behavior customization."""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from .base import BaseIOSchema
from .utils import create_identifier_validator


class TraitConfig(BaseIOSchema):
    """Configuration schema for an agent trait."""
    
    name: str = Field(description="Human-readable trait name (e.g., 'Funny', 'Customer Obsessed')")
    description: Optional[str] = Field(default=None, description="Human-readable trait description")
    instructions: str = Field(description="Specific instructions for this trait behavior")
    weight: float = Field(default=1.0, ge=0.0, le=2.0, description="Trait influence weight")
    
    # Note: name is kept as display name, identifier is handled separately by the loader
    
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
        # Check for potential prompt injection patterns
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


class TraitApplication(BaseIOSchema):
    """Schema for applying traits to agent behavior."""
    
    traits: List[TraitConfig] = Field(description="List of traits to apply to agent")
    combination_strategy: str = Field(default="weighted", description="How to combine multiple traits")
    max_traits: int = Field(default=5, ge=1, le=10, description="Maximum number of traits per agent")
    
    @validator('traits')
    def validate_trait_uniqueness(cls, v):
        """Ensure trait names are unique within an agent."""
        names = [trait.name for trait in v]
        if len(names) != len(set(names)):
            raise ValueError('Trait names must be unique within an agent')
        return v


class TraitValidationResult(BaseIOSchema):
    """Result of trait validation operations."""
    
    is_valid: bool = Field(description="Whether trait configuration is valid")
    errors: List[str] = Field(default=[], description="List of validation errors")
    warnings: List[str] = Field(default=[], description="List of validation warnings")
    processed_traits: List[TraitConfig] = Field(default=[], description="Successfully processed traits")