"""Knowledge base registry for managing descriptions and metadata."""

import logging
from typing import Dict


class KnowledgeRegistry:
    """Registry for managing knowledge base descriptions and metadata."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.knowledge_descriptions: Dict[str, str] = {}
    
    def register_description(self, kb_key: str, description: str) -> None:
        """
        Register a description for a knowledge base.
        
        Args:
            kb_key: Knowledge base key (ID or name)
            description: Knowledge base description
        """
        self.knowledge_descriptions[kb_key] = description
        self.logger.debug(f"Registered description for knowledge base '{kb_key}': {description}")
    
    def get_description(self, kb_key: str) -> str:
        """
        Get description for a knowledge base.
        
        Args:
            kb_key: Knowledge base key (ID or name)
            
        Returns:
            Knowledge base description or empty string if not found
        """
        return self.knowledge_descriptions.get(kb_key, "")
    
    def get_all_descriptions(self) -> Dict[str, str]:
        """
        Get all knowledge base descriptions.
        
        Returns:
            Dictionary of knowledge base keys to descriptions
        """
        return self.knowledge_descriptions.copy()
    
    def has_knowledge_bases(self) -> bool:
        """
        Check if any knowledge bases are registered.
        
        Returns:
            True if knowledge bases are registered, False otherwise
        """
        return len(self.knowledge_descriptions) > 0