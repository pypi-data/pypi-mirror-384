"""
Knowledge manager for coordinating multiple knowledge bases.
"""

import logging
from typing import Any, Dict, List, Optional

from .base import BaseKnowledgeBase, KnowledgeQuery, KnowledgeResult, KnowledgeProvider
from .embedchain_adapter import EmbedchainProvider
from .opensearch_adapter import OpenSearchProvider
from ..core.cache import CacheManager, CacheConfig, CacheStatus
from ..core.cache.hashers import ConfigHasher
from ..core.exceptions import KnowledgeError


class KnowledgeManager:
    """
    Central manager for all knowledge bases in a team.
    
    This class coordinates multiple knowledge bases and provides a unified
    interface for querying and managing knowledge across the system.
    """
    
    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize the knowledge manager.
        
        Args:
            cache_dir: Optional directory for cache files
        """
        self.knowledge_bases: Dict[str, BaseKnowledgeBase] = {}
        self.providers: Dict[str, KnowledgeProvider] = {}
        self.logger = logging.getLogger(__name__)
        
        # Initialize generic cache system for knowledge bases
        if cache_dir is None:
            import os
            cache_dir = os.path.join(os.getcwd(), '.cache', 'knowledge')
        
        cache_config = CacheConfig(
            cache_dir=cache_dir,
            cache_name="knowledge_cache",
            hash_strategy=ConfigHasher(),
            auto_cleanup=True
        )
        self.cache = CacheManager(cache_config)
        
        # Register default providers
        self._register_default_providers()
    
    def _register_default_providers(self) -> None:
        """Register default knowledge providers."""
        try:
            embedchain_provider = EmbedchainProvider(self.cache)
            self.register_provider('embedchain', embedchain_provider)
            self.logger.debug("Registered Embedchain provider with generic cache support")
        except ImportError:
            self.logger.warning("Embedchain not available, skipping provider registration")
        
        try:
            opensearch_provider = OpenSearchProvider(self.cache)
            self.register_provider('opensearch', opensearch_provider)
            self.logger.debug("Registered OpenSearch provider with generic cache support")
        except ImportError:
            self.logger.warning("OpenSearch dependencies not available, skipping provider registration")
    
    def register_provider(self, name: str, provider: KnowledgeProvider) -> None:
        """
        Register a knowledge provider.
        
        Args:
            name: Provider name
            provider: Provider instance
        """
        self.providers[name] = provider
        self.logger.info(f"Registered knowledge provider: {name}")
    
    def create_knowledge_base(
        self, 
        name: str, 
        kb_type: str, 
        config: Optional[Dict[str, Any]] = None,
        knowledge_id: Optional[str] = None
    ) -> BaseKnowledgeBase:
        """
        Create a new knowledge base.
        
        Args:
            name: Knowledge base name
            kb_type: Type of knowledge base
            config: Optional configuration
            knowledge_id: Optional unique identifier for the knowledge base
            
        Returns:
            Created knowledge base instance
            
        Raises:
            KnowledgeError: If creation fails
        """
        if name in self.knowledge_bases:
            raise KnowledgeError(f"Knowledge base '{name}' already exists")
        
        # Knowledge ID is required - should not fall back to name
        if not knowledge_id:
            knowledge_id = (config or {}).get('id')
            if not knowledge_id:
                raise KnowledgeError(f"Knowledge ID is required for knowledge base '{name}'")
        
        # Find a provider - respect explicit provider configuration first
        provider = None
        explicit_provider = config.get('provider') if config else None
        
        if explicit_provider:
            # Use explicitly specified provider if available and supports the type
            if explicit_provider in self.providers:
                provider_instance = self.providers[explicit_provider]
                if kb_type in provider_instance.get_supported_types():
                    provider = provider_instance
                    self.logger.info(f"Using explicitly configured provider '{explicit_provider}' for knowledge base '{name}'")
                else:
                    self.logger.warning(f"Explicitly configured provider '{explicit_provider}' does not support type '{kb_type}'")
            else:
                self.logger.warning(f"Explicitly configured provider '{explicit_provider}' not available")
        
        # Fall back to first available provider that supports the type
        if not provider:
            for provider_name, provider_instance in self.providers.items():
                if kb_type in provider_instance.get_supported_types():
                    provider = provider_instance
                    self.logger.info(f"Using fallback provider '{provider_name}' for knowledge base '{name}'")
                    break
        
        if not provider:
            available_providers = list(self.providers.keys())
            raise KnowledgeError(f"No provider found for knowledge base type '{kb_type}'. Available providers: {available_providers}")
        
        try:
            # Check if provider supports knowledge_id parameter
            if hasattr(provider.create_knowledge_base, '__code__') and 'knowledge_id' in provider.create_knowledge_base.__code__.co_varnames:
                kb = provider.create_knowledge_base(name, kb_type, config, knowledge_id)
            else:
                kb = provider.create_knowledge_base(name, kb_type, config)
            
            self.knowledge_bases[name] = kb
            self.logger.info(f"Created knowledge base '{name}' (ID: {knowledge_id}) of type '{kb_type}'")
            return kb
        except Exception as e:
            raise KnowledgeError(f"Failed to create knowledge base '{name}': {e}")
    
    def get_knowledge_base(self, name: str) -> Optional[BaseKnowledgeBase]:
        """
        Get a knowledge base by name.
        
        Args:
            name: Knowledge base name
            
        Returns:
            Knowledge base instance or None if not found
        """
        return self.knowledge_bases.get(name)
    
    def knowledge_base_exists(self, name: str) -> bool:
        """
        Check if a knowledge base exists (is registered).
        
        Args:
            name: Knowledge base name
            
        Returns:
            True if knowledge base exists
        """
        return name in self.knowledge_bases
    
    def is_knowledge_base_loaded(self, knowledge_id: str) -> bool:
        """
        Check if a knowledge base is loaded in cache.
        
        Args:
            knowledge_id: Knowledge base identifier
            
        Returns:
            True if knowledge base is loaded in cache
        """
        cache_entry = self.cache._cache.get(knowledge_id)
        if cache_entry:
            return cache_entry.status == CacheStatus.LOADED
        return False
    
    async def add_data_to_knowledge_base(
        self, 
        kb_name: str, 
        data: str, 
        source: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Add data to a knowledge base.
        
        Args:
            kb_name: Knowledge base name
            data: Data to add
            source: Optional source identifier
            metadata: Optional metadata
            
        Returns:
            Number of documents successfully added
            
        Raises:
            KnowledgeError: If knowledge base not found or addition fails
        """
        kb = self.get_knowledge_base(kb_name)
        if not kb:
            raise KnowledgeError(f"Knowledge base '{kb_name}' not found")
        
        if not kb.is_initialized():
            await kb.initialize()
        
        try:
            # For OpenSearch adapter, this returns document count
            # For other adapters that don't support it yet, we'll handle the TypeError
            try:
                doc_count = await kb.add_data(data, source or data[:50], metadata)
                self.logger.debug(f"Added {doc_count} documents to knowledge base '{kb_name}'")
                return doc_count
            except TypeError:
                # Legacy adapter that doesn't return count
                await kb.add_data(data, source or data[:50], metadata)
                self.logger.debug(f"Added data to knowledge base '{kb_name}' (count not available)")
                return 1  # Default to 1 for backward compatibility
        except Exception as e:
            raise KnowledgeError(f"Failed to add data to knowledge base '{kb_name}': {e}")
    
    async def query_knowledge_base(
        self, 
        kb_name: str, 
        query: str, 
        max_results: int = 5
    ) -> List[KnowledgeResult]:
        """
        Query a specific knowledge base.
        
        Args:
            kb_name: Knowledge base name
            query: Query string
            max_results: Maximum number of results
            
        Returns:
            List of knowledge results
            
        Raises:
            KnowledgeError: If knowledge base not found or query fails
        """
        kb = self.get_knowledge_base(kb_name)
        if not kb:
            raise KnowledgeError(f"Knowledge base '{kb_name}' not found")
        
        if not kb.is_initialized():
            await kb.initialize()
        
        try:
            results = await kb.query(query, max_results)
            self.logger.debug(f"Queried knowledge base '{kb_name}' with {len(results)} results")
            return results
        except Exception as e:
            raise KnowledgeError(f"Failed to query knowledge base '{kb_name}': {e}")
    
    async def query_all_knowledge_bases(
        self, 
        query: str, 
        max_results_per_kb: int = 3
    ) -> Dict[str, List[KnowledgeResult]]:
        """
        Query all available knowledge bases.
        
        Args:
            query: Query string
            max_results_per_kb: Maximum results per knowledge base
            
        Returns:
            Dictionary mapping knowledge base names to results
        """
        all_results = {}
        
        for kb_name in self.knowledge_bases:
            try:
                results = await self.query_knowledge_base(kb_name, query, max_results_per_kb)
                if results:
                    all_results[kb_name] = results
            except Exception as e:
                self.logger.warning(f"Failed to query knowledge base '{kb_name}': {e}")
        
        return all_results
    
    def list_knowledge_bases(self) -> List[str]:
        """
        List all available knowledge base names.
        
        Returns:
            List of knowledge base names
        """
        return list(self.knowledge_bases.keys())
    
    def get_knowledge_base_info(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a knowledge base.
        
        Args:
            name: Knowledge base name
            
        Returns:
            Dictionary with knowledge base information or None if not found
        """
        kb = self.get_knowledge_base(name)
        if not kb:
            return None
        
        return {
            'name': kb.name,
            'initialized': kb.is_initialized(),
            'config': kb.config
        }
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        stats = self.cache.get_stats()
        
        # Convert to a format similar to the old interface for compatibility
        by_status = stats.get('by_status', {})
        return {
            'total_entries': stats['total_entries'],
            'loaded': by_status.get('loaded', 0),
            'loading': by_status.get('loading', 0),
            'failed': by_status.get('failed', 0),
            'cache_dir': stats['cache_dir'],
            'hash_strategy': stats['hash_strategy']
        }
    
    def get_detailed_cache_stats(self) -> Dict[str, Any]:
        """
        Get detailed cache statistics from the generic cache system.
        
        Returns:
            Detailed statistics dictionary
        """
        return self.cache.get_stats()
    
    def invalidate_knowledge_cache(self, knowledge_id: str) -> None:
        """
        Invalidate the cache for a specific knowledge base.
        
        Args:
            knowledge_id: Knowledge base identifier to invalidate
        """
        success = self.cache.invalidate(knowledge_id)
        if success:
            self.logger.info(f"Invalidated cache for knowledge base '{knowledge_id}'")
        else:
            self.logger.warning(f"Knowledge base '{knowledge_id}' not found in cache")
    
    def cleanup_failed_cache_entries(self) -> None:
        """Clean up failed cache entries."""
        count = self.cache.cleanup_failed()
        if count > 0:
            self.logger.info(f"Cleaned up {count} failed cache entries")
    
    def list_cached_knowledge_bases(self) -> List[str]:
        """
        Get all cached knowledge base IDs.
        
        Returns:
            List of cached knowledge base IDs
        """
        knowledge_entries = self.cache.list_by_type("knowledge_base")
        return [entry.cache_key for entry in knowledge_entries]
    
    def get_loaded_knowledge_bases(self) -> List[str]:
        """
        Get all successfully loaded knowledge base IDs.
        
        Returns:
            List of loaded knowledge base IDs
        """
        loaded_entries = self.cache.list_by_status(CacheStatus.LOADED)
        return [entry.cache_key for entry in loaded_entries if entry.item_type == "knowledge_base"]
    
    async def cleanup(self) -> None:
        """Clean up all knowledge bases."""
        for kb in self.knowledge_bases.values():
            try:
                await kb.cleanup()
            except Exception as e:
                self.logger.warning(f"Error cleaning up knowledge base '{kb.name}': {e}")
        
        self.knowledge_bases.clear()
        self.logger.info("Knowledge manager cleanup completed")