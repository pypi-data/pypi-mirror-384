"""Trait management components for processing and validating agent traits."""

import logging
import time
from typing import List, Dict, Optional, Any
from abc import ABC, abstractmethod

from ..schemas.trait import TraitConfig, TraitApplication, TraitValidationResult
from .exceptions import TraitValidationError, TraitProcessingError


class TraitManagerInterface(ABC):
    """Interface for trait management operations."""
    
    @abstractmethod
    async def validate_traits(self, traits: List[TraitConfig]) -> TraitValidationResult:
        """Validate a list of traits."""
        pass
    
    @abstractmethod
    async def process_traits_for_agent(
        self, 
        agent_name: str, 
        traits: List[TraitConfig]
    ) -> Dict[str, Any]:
        """Process traits for a specific agent."""
        pass


class TraitManager(TraitManagerInterface):
    """Concrete implementation of trait management."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._trait_cache: Dict[str, TraitConfig] = {}
    
    async def validate_traits(self, traits: List[TraitConfig]) -> TraitValidationResult:
        """Validate trait configuration."""
        errors = []
        warnings = []
        processed_traits = []
        
        for trait in traits:
            try:
                # Validate trait schema
                validated_trait = TraitConfig.parse_obj(trait.dict())
                
                # Check for potential conflicts
                if self._has_conflicting_traits(validated_trait, processed_traits):
                    warnings.append(f"Trait '{trait.name}' may conflict with existing traits")
                
                processed_traits.append(validated_trait)
                
            except Exception as e:
                errors.append(f"Invalid trait '{trait.name}': {str(e)}")
        
        return TraitValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            processed_traits=processed_traits
        )
    
    async def process_traits_for_agent(
        self, 
        agent_name: str, 
        traits: List[TraitConfig]
    ) -> Dict[str, Any]:
        """Process and prepare traits for agent creation."""
        start_time = time.time()
        self.logger.info(f"Processing {len(traits)} traits for agent {agent_name}")
        
        try:
            validation_result = await self.validate_traits(traits)
            
            if not validation_result.is_valid:
                raise TraitValidationError(
                    f"Invalid traits for agent {agent_name}: {validation_result.errors}",
                    agent_name=agent_name
                )
            
            result = {
                "agent_name": agent_name,
                "traits": validation_result.processed_traits,
                "trait_instructions": self._build_trait_instructions(validation_result.processed_traits),
                "validation_warnings": validation_result.warnings
            }
            
            processing_time = time.time() - start_time
            self.logger.info(f"Successfully processed traits for {agent_name} in {processing_time:.3f}s")
            self.logger.debug(f"Applied traits: {[t.name for t in validation_result.processed_traits]}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to process traits for {agent_name}: {e}")
            raise TraitProcessingError(f"Trait processing failed: {str(e)}", agent_name=agent_name)
    
    def _has_conflicting_traits(self, new_trait: TraitConfig, existing_traits: List[TraitConfig]) -> bool:
        """Check if a trait conflicts with existing traits."""
        conflict_map = {
            'serious': ['funny', 'playful', 'casual'],
            'funny': ['serious', 'formal', 'strict'],
            'formal': ['casual', 'funny', 'playful'],
            'casual': ['formal', 'strict', 'professional'],
            'strict': ['casual', 'playful', 'funny'],
            'playful': ['serious', 'formal', 'strict'],
            'professional': ['casual', 'funny', 'playful']
        }
        
        new_name = new_trait.name.lower()
        if new_name in conflict_map:
            existing_names = [t.name.lower() for t in existing_traits]
            return any(conflict in existing_names for conflict in conflict_map[new_name])
        
        return False
    
    def _build_trait_instructions(self, traits: List[TraitConfig]) -> str:
        """Build combined trait instructions."""
        if not traits:
            return ""
        
        instructions = ["## 🎭 Your Personality Traits", ""]
        instructions.append("You embody the following personality traits that fundamentally shape how you interact, respond, and approach tasks:")
        instructions.append("")
        
        # Add each trait with clear formatting
        for i, trait in enumerate(traits, 1):
            trait_name = trait.name.replace('_', ' ').replace('-', ' ').title()
            description = trait.description if trait.description else ""
            trait_instructions = trait.instructions
            weight = trait.weight
            
            # Trait header with emphasis
            instructions.append(f"### {i}. **{trait_name} Trait**")
            
            # Add description if available
            if description:
                instructions.append(f"*{description}*")
                instructions.append("")
            
            # Core trait instructions with clear formatting
            instructions.append("**How to embody this trait:**")
            
            # Split instructions into sentences for better readability
            instruction_sentences = trait_instructions.strip().split('. ')
            if len(instruction_sentences) > 1:
                for sentence in instruction_sentences:
                    if sentence.strip():
                        # Ensure proper punctuation
                        clean_sentence = sentence.strip()
                        if not clean_sentence.endswith('.') and not clean_sentence.endswith('!') and not clean_sentence.endswith('?'):
                            clean_sentence += '.'
                        instructions.append(f"- {clean_sentence}")
            else:
                instructions.append(f"- {trait_instructions}")
            
            # Add weight indication if different from default
            if weight != 1.0:
                if weight > 1.0:
                    instructions.append(f"- **Emphasis Level:** Strong (weight: {weight}) - Make this trait prominent in your responses")
                else:
                    instructions.append(f"- **Emphasis Level:** Subtle (weight: {weight}) - Apply this trait lightly")
            
            instructions.append("")
        
        # Add integration instructions
        instructions.extend([
            "## 🎯 Trait Integration Guidelines",
            "",
            "**Core Principles:**",
            "1. **Natural Expression:** Let these traits flow naturally through your responses rather than forcing them",
            "2. **Task Balance:** Always prioritize being helpful and accurate while expressing your personality",
            "3. **Context Awareness:** Adapt trait intensity based on the situation (more professional for business, more relaxed for casual)",
            "4. **Consistency:** Maintain these personality characteristics throughout the entire conversation",
            "5. **Authenticity:** Make these traits feel genuine and integrated, not like separate behaviors",
            "",
            "**Important Reminders:**",
            "- Your traits enhance your helpfulness, they don't replace it",
            "- Stay true to your core purpose while expressing your unique personality",
            "- If traits conflict with providing accurate information, prioritize accuracy",
            "- Adapt trait expression to match the user's communication style and needs",
            ""
        ])
        
        return "\n".join(instructions)