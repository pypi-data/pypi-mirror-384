"""Knowledge base loading functionality."""

import logging
from typing import List, Dict, Any, Optional

from ...knowledge import KnowledgeManager
from .knowledge_registry import KnowledgeRegistry


class KnowledgeLoader:
    """Handles loading and initialization of knowledge bases."""
    
    def __init__(self, knowledge_registry: KnowledgeRegistry = None, progress_callback=None):
        self.knowledge_registry = knowledge_registry or KnowledgeRegistry()
        self.knowledge_manager: Optional[KnowledgeManager] = None
        self.progress_callback = progress_callback
        self.logger = logging.getLogger(__name__)
    
    def ensure_knowledge_manager(self):
        """Ensure knowledge manager is initialized."""
        if self.knowledge_manager is None:
            try:
                self.knowledge_manager = KnowledgeManager()
            except ImportError as e:
                self.logger.warning(f"Knowledge manager not available: {e}")
    
    async def load_knowledge_bases(self, knowledge_config: List[Dict[str, Any]]) -> None:
        """
        Load knowledge bases from configuration.
        
        Args:
            knowledge_config: List of knowledge base configurations from YAML
        """
        self.ensure_knowledge_manager()
        if self.knowledge_manager is None:
            self.logger.warning("Knowledge manager not available, skipping knowledge base loading")
            return
        
        # Show initialization indicator if there are knowledge bases to load
        if knowledge_config:
            message = "Initializing knowledge bases..."
            if self.progress_callback:
                self.progress_callback(message)
            else:
                print(message, flush=True)
        
        for kb_config in knowledge_config:
            await self._load_single_knowledge_base(kb_config)
    
    async def _load_single_knowledge_base(self, kb_config: Dict[str, Any]) -> None:
        """Load a single knowledge base from configuration."""
        # Ensure knowledge manager is initialized
        self.ensure_knowledge_manager()
        if self.knowledge_manager is None:
            self.logger.warning("Knowledge manager not available, skipping knowledge base loading")
            return
            
        name = kb_config.get('name')
        kb_type = kb_config.get('type')
        kb_id = kb_config.get('id')
        
        # Validate required fields
        if not kb_type:
            error_msg = f"Invalid knowledge base configuration - missing required 'type': {kb_config}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        
        if not kb_id:
            error_msg = f"Invalid knowledge base configuration - missing required 'id': {kb_config}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        
        if not name:
            error_msg = f"Invalid knowledge base configuration - missing required 'name': {kb_config}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Store knowledge description if provided
        description = kb_config.get('description')
        if description:
            self.knowledge_registry.register_description(kb_id, description)
            self.logger.info(f"Stored description for knowledge base '{kb_id}': {description}")
        
        try:
            # Check if knowledge base already exists
            existing_kb = self.knowledge_manager.get_knowledge_base(kb_id)
            if existing_kb:
                self.logger.info(f"Knowledge base '{kb_id}' already exists, skipping creation")
                # Still try to add data if specified
                data = kb_config.get('data')
                if data:
                    await self._add_data_to_knowledge_base(kb_id, data)
                return
            
            # Show loading indicator
            message = f"Loading Knowledge Source {name}..."
            if self.progress_callback:
                self.progress_callback(message)
            else:
                print(message, flush=True)
            self.logger.info(f"Loading Knowledge Source {name} (ID: {kb_id})...")
            
            # Create knowledge base using ID as the primary identifier
            embedchain_config = kb_config.get('config')
            config_with_id = embedchain_config.copy() if embedchain_config else {}
            config_with_id['id'] = kb_id
            
            # Include data sources in config for cache validation
            data = kb_config.get('data')
            if data:
                config_with_id['data'] = data
            
            self.knowledge_manager.create_knowledge_base(
                name=kb_id,  # Use ID as the key for the knowledge manager
                kb_type=kb_type, 
                config=config_with_id,
                knowledge_id=kb_id  # Pass knowledge_id explicitly
            )
            
            # Add data if specified
            data = kb_config.get('data')
            if data:
                await self._add_data_to_knowledge_base(kb_id, data)
            
            self.logger.info(f"Successfully loaded knowledge base '{name}' (ID: {kb_id}) of type '{kb_type}'")
            
        except Exception as e:
            self.logger.error(f"Failed to load knowledge base '{name}' (ID: {kb_id}): {e}")
    
    async def _add_data_to_knowledge_base(self, kb_key: str, data: Any) -> None:
        """Add data to a knowledge base."""
        # Always treat data as a list for consistency
        if isinstance(data, list):
            data_list = data
        else:
            data_list = [data]
        
        # Add each data item to the knowledge base
        for item in data_list:
            self.logger.info(f"Adding data to knowledge base '{kb_key}': {item}")
            await self.knowledge_manager.add_data_to_knowledge_base(kb_key, item)
    
    def add_knowledge_tools(self, agent_tools: List[str], knowledge_names: List[str]) -> List[str]:
        """
        Add knowledge query tools for specified knowledge bases to the agent's tool list.
        
        Args:
            agent_tools: Current list of agent tools
            knowledge_names: List of knowledge base names to add tools for
            
        Returns:
            Updated list of agent tools including knowledge query tools
        """
        if self.knowledge_manager is None:
            self.logger.warning("Knowledge manager not available, skipping knowledge tools")
            return agent_tools
        
        # Check if knowledge_query tool is already in the list
        if 'knowledge_query' not in agent_tools:
            agent_tools.append('knowledge_query')
            self.logger.info("Added knowledge_query tool to agent")
        
        return agent_tools