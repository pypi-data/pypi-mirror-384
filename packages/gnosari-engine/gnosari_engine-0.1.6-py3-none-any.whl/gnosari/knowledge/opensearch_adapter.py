"""
OpenSearch adapter for integrating OpenSearch knowledge bases with Gnosari.
"""

import logging
import os
import re
from typing import Any, Dict, List, Optional

from .base import BaseKnowledgeBase, KnowledgeResult, KnowledgeProvider
from .loaders import BaseLoader, WebsiteLoader, SitemapLoader
from ..core.cache import CacheManager, CacheStatus
from ..engine.config.env_substitutor import EnvironmentVariableSubstitutor
from ..core.exceptions import KnowledgeError


class OpenSearchKnowledgeBase(BaseKnowledgeBase):
    """
    OpenSearch implementation of the knowledge base interface.
    """
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None, 
                 knowledge_id: Optional[str] = None, cache: Optional[CacheManager] = None):
        """
        Initialize the OpenSearch knowledge base.
        
        Args:
            name: Knowledge base name
            config: Optional OpenSearch configuration
            knowledge_id: Unique identifier for the knowledge base (used as index name)
            cache: Optional generic cache manager instance
        """
        super().__init__(name, config)
        self.knowledge_id = knowledge_id or name
        self.opensearch_client = None
        self.cache = cache
        self.logger = logging.getLogger(__name__)
        
        # Configuration for OpenSearch connection with environment variable substitution
        raw_opensearch_config = self.config.get('opensearch', {})
        env_substitutor = EnvironmentVariableSubstitutor()
        self.opensearch_config = env_substitutor.substitute(raw_opensearch_config)
        self.index_name = f"gnosari_{self.knowledge_id}"
        
        # Model configuration - check both top-level and opensearch-specific config
        self.model_id = (
            self.config.get('model_id') or 
            self.opensearch_config.get('model_id') or
            os.getenv('OPENSEARCH_MODEL_ID')
        )
        if not self.model_id:
            self.logger.warning(f"No model_id specified for OpenSearch knowledge base '{name}'. Check config.model_id, config.opensearch.model_id, or OPENSEARCH_MODEL_ID environment variable.")
    
    async def initialize(self) -> None:
        """Initialize the OpenSearch client and index."""
        if self._initialized:
            return
        
        try:
            from opensearchpy import OpenSearch
            
            # Build OpenSearch client configuration
            opensearch_host = self.opensearch_config.get('host', 'localhost')
            opensearch_port = int(self.opensearch_config.get('port', 9200))
            use_ssl = self._to_bool(self.opensearch_config.get('use_ssl', False))
            verify_certs = self._to_bool(self.opensearch_config.get('verify_certs', False))
            username = self.opensearch_config.get('username')
            password = self.opensearch_config.get('password')
            ca_certs = self.opensearch_config.get('ca_certs')
            
            client_config = {
                'hosts': [{'host': opensearch_host, 'port': opensearch_port}],
                'http_compress': True,
                'use_ssl': use_ssl,
                'verify_certs': verify_certs,
                'ssl_assert_hostname': False,
                'ssl_show_warn': False,
                'timeout': self.opensearch_config.get('timeout', 30),
            }
            
            if ca_certs:
                client_config['ca_certs'] = ca_certs
            
            if username and password:
                client_config['http_auth'] = (username, password)
            
            self.opensearch_client = OpenSearch(**client_config)
            
            # Check if index exists, create if it doesn't
            if not self.opensearch_client.indices.exists(index=self.index_name):
                await self._create_index()
            
            self._initialized = True
            self.logger.info(f"Initialized OpenSearch knowledge base '{self.name}' with index '{self.index_name}'")
            
        except ImportError:
            raise KnowledgeError("opensearch-py not installed. Install with: pip install opensearch-py")
        except Exception as e:
            raise KnowledgeError(f"Failed to initialize OpenSearch knowledge base '{self.name}': {e}")
    
    async def _create_index(self) -> None:
        """Create the OpenSearch index for this knowledge base with automatic embedding generation."""
        # Get pipeline configuration - check if ingest pipeline should be used
        pipeline_name = self.opensearch_config.get('pipeline_name', os.getenv('OPENSEARCH_PIPELINE_NAME'))
        
        # Default index mapping for text search and embeddings
        index_mapping = {
            "settings": {
                "index": {
                    "knn": True,
                    "number_of_shards": self.opensearch_config.get('number_of_shards', 1),
                    "number_of_replicas": self.opensearch_config.get('number_of_replicas', 1)
                }
            },
            "mappings": {
                "properties": {
                    "text": {
                        "type": "text"
                    },
                    "text_embedding": {
                        "type": "knn_vector",
                        "dimension": self.opensearch_config.get('embedding_dimension', 1536),
                        "method": {
                            "name": "hnsw",
                            "space_type": "cosinesimil",
                            "engine": "nmslib",
                            "parameters": {
                                "ef_construction": 512,
                                "m": 16
                            }
                        }
                    },
                    "metadata": {
                        "type": "object"
                    },
                    "timestamp": {
                        "type": "date"
                    }
                }
            }
        }
        
        # Add ingest pipeline to index settings if available
        if pipeline_name and self.model_id:
            index_mapping["settings"]["index"]["default_pipeline"] = pipeline_name
            self.logger.info(f"Configured index to use ingest pipeline: {pipeline_name}")
        elif self.model_id:
            self.logger.warning(f"Model ID available ({self.model_id}) but no pipeline_name configured. Embeddings will not be generated automatically.")
        
        self.opensearch_client.indices.create(
            index=self.index_name,
            body=index_mapping
        )
        self.logger.info(f"Created OpenSearch index: {self.index_name}")
    
    async def add_data(self, data: str, source: str, metadata: Optional[Dict[str, Any]] = None) -> int:
        """
        Add data to the OpenSearch knowledge base.
        
        Args:
            data: Data content or URL to add
            source: Source identifier
            metadata: Optional metadata
            
        Returns:
            Number of documents successfully indexed
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # For multiple data sources, we need to check if this specific data source 
            # was already processed while allowing other sources to be processed
            if self.cache:
                cache_entry = self.cache._cache.get(self.knowledge_id)
                if cache_entry and cache_entry.status.value == "loaded":
                    # Check if the current data source was already processed
                    if data in cache_entry.data_sources:
                        self.logger.info(f"Data source '{data}' already processed for knowledge base '{self.name}'")
                        return 0
                    else:
                        self.logger.info(f"Adding new data source '{data}' to existing knowledge base '{self.name}'")
            
            # Update cache with current data source
            if self.cache:
                # Get existing data sources and add current one
                cache_entry = self.cache._cache.get(self.knowledge_id)
                existing_sources = cache_entry.data_sources if cache_entry else []
                if data not in existing_sources:
                    updated_sources = existing_sources + [data]
                else:
                    updated_sources = existing_sources
                
                self.cache.mark_loading(
                    cache_key=self.knowledge_id,
                    item_type="knowledge_base",
                    data=self.config,
                    data_sources=updated_sources,
                    metadata={'name': self.name, 'data_source': data, 'source': source}
                )
            
            self.logger.info(f'Adding data to OpenSearch knowledge base {self.name} (index: {self.index_name}): {data}')
            
            # Get the loader for the knowledge base type
            kb_type = self.config.get('type', '').lower()
            loader = self._get_loader(kb_type)
            
            # Load data using the appropriate loader
            documents = await loader.load_data(data, metadata)
            
            # Index documents in OpenSearch using bulk API for efficiency
            if documents:
                bulk_body = []
                for i, doc in enumerate(documents):
                    doc_id = f"{source}_{i}"
                    
                    # Add index operation metadata
                    bulk_body.append({
                        "index": {
                            "_index": self.index_name,
                            "_id": doc_id
                        }
                    })
                    # Add document body
                    bulk_body.append(doc)
                
                # Perform bulk indexing - embeddings will be generated automatically by ingest pipeline if configured
                try:
                    response = self.opensearch_client.bulk(body=bulk_body)
                    
                    # Check for bulk operation errors
                    if response.get('errors'):
                        failed_items = [item for item in response['items'] if 'error' in item.get('index', {})]
                        if failed_items:
                            self.logger.warning(f"Some documents failed to index: {len(failed_items)} failures out of {len(documents)} documents")
                            for item in failed_items[:3]:  # Log first 3 failures for debugging
                                error = item['index'].get('error', {})
                                self.logger.warning(f"Index error: {error.get('reason', 'Unknown error')}")
                    else:
                        if self.model_id:
                            self.logger.debug(f"Bulk indexed {len(documents)} documents - embeddings will be generated by ingest pipeline")
                        else:
                            self.logger.debug(f"Bulk indexed {len(documents)} documents")
                            
                except Exception as e:
                    raise KnowledgeError(f"Bulk indexing failed for knowledge base '{self.name}': {e}")
            
            # Refresh index to make documents searchable
            self.opensearch_client.indices.refresh(index=self.index_name)
            
            # Mark as successfully loaded in cache
            if self.cache:
                self.cache.mark_loaded(self.knowledge_id, {'data_source': data, 'source': source})
            
            self.logger.debug(f"Added {len(documents)} documents to OpenSearch knowledge base '{self.name}' (index: {self.index_name}): {source}")
            return len(documents)
            
        except Exception as e:
            # Mark as failed in cache
            if self.cache:
                self.cache.mark_failed(self.knowledge_id, str(e))
            raise KnowledgeError(f"Failed to add data to knowledge base '{self.name}': {e}")
    
    def _get_loader(self, kb_type: str) -> BaseLoader:
        """Get the appropriate loader for the knowledge base type."""
        loader_config = self.config.get('loader_config', {})
        
        if kb_type == 'website':
            return WebsiteLoader(loader_config)
        elif kb_type == 'sitemap':
            return SitemapLoader(loader_config)
        else:
            # Default to website loader for unknown types
            self.logger.warning(f"Unknown knowledge base type '{kb_type}', using WebsiteLoader")
            return WebsiteLoader(loader_config)
    
    @staticmethod
    def _to_bool(value) -> bool:
        """Convert string or other value to boolean."""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes', 'on')
        return bool(value)
    
    async def query(self, query: str, max_results: int = 5) -> List[KnowledgeResult]:
        """
        Query the OpenSearch knowledge base.
        
        Args:
            query: Query string
            max_results: Maximum number of results
            
        Returns:
            List of knowledge results
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Use semantic search if model_id is available, otherwise use text search
            if self.model_id:
                search_body = {
                    "query": {
                        "neural": {
                            "text_embedding": {
                                "query_text": query,
                                "model_id": self.model_id,
                                "k": max_results * 2  # Get more candidates for better results
                            }
                        }
                    },
                    "size": max_results,
                    "_source": ["text", "metadata", "timestamp"]
                }
            else:
                # Fall back to text search
                search_body = {
                    "query": {
                        "match": {
                            "text": query
                        }
                    },
                    "size": max_results,
                    "_source": ["text", "metadata", "timestamp"]
                }
            
            response = self.opensearch_client.search(
                index=self.index_name,
                body=search_body
            )
            
            # Convert OpenSearch results to KnowledgeResult objects
            results = []
            hits = response.get('hits', {}).get('hits', [])
            
            for hit in hits:
                source_doc = hit['_source']
                results.append(
                    KnowledgeResult(
                        content=source_doc.get('text', ''),
                        source=source_doc.get('metadata', {}).get('source', hit['_id']),
                        score=hit['_score'],
                        metadata=source_doc.get('metadata', {})
                    )
                )
            
            self.logger.info(f"OpenSearch knowledge base '{self.name}' returned {len(results)} results for query: {query}")
            return results
            
        except Exception as e:
            raise KnowledgeError(f"Failed to query knowledge base '{self.name}': {e}")
    
    async def delete_data(self, source: str) -> bool:
        """
        Delete data from the OpenSearch knowledge base.
        
        Args:
            source: Source identifier
            
        Returns:
            True if data was deleted
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Delete documents by source in metadata
            delete_query = {
                "query": {
                    "term": {
                        "metadata.source": source
                    }
                }
            }
            
            response = self.opensearch_client.delete_by_query(
                index=self.index_name,
                body=delete_query
            )
            
            deleted_count = response.get('deleted', 0)
            self.logger.info(f"Deleted {deleted_count} documents with source '{source}' from knowledge base '{self.name}'")
            return deleted_count > 0
            
        except Exception as e:
            self.logger.error(f"Failed to delete data from knowledge base '{self.name}': {e}")
            return False
    
    async def cleanup(self) -> None:
        """Clean up OpenSearch resources."""
        if self.opensearch_client:
            try:
                # Optionally delete the index
                if self.opensearch_client.indices.exists(index=self.index_name):
                    # Don't delete index by default to preserve data
                    pass
            except Exception as e:
                self.logger.warning(f"Error during cleanup of knowledge base '{self.name}': {e}")
            finally:
                self.opensearch_client = None
        
        self._initialized = False


class OpenSearchProvider(KnowledgeProvider):
    """
    Provider for creating OpenSearch knowledge bases.
    """
    
    def __init__(self, cache: Optional[CacheManager] = None):
        """
        Initialize the OpenSearch provider.
        
        Args:
            cache: Optional generic cache manager instance
        """
        self.cache = cache
        self.logger = logging.getLogger(__name__)
    
    def create_knowledge_base(
        self, 
        name: str, 
        kb_type: str, 
        config: Optional[Dict[str, Any]] = None,
        knowledge_id: Optional[str] = None
    ) -> BaseKnowledgeBase:
        """
        Create an OpenSearch knowledge base.
        
        Args:
            name: Knowledge base name
            kb_type: Type (should be supported by OpenSearch provider)
            config: Optional configuration
            knowledge_id: Optional unique identifier for the knowledge base
            
        Returns:
            OpenSearchKnowledgeBase instance
        """
        # Create the full config including the type
        full_config = config or {}
        full_config['type'] = kb_type
        
        # Knowledge ID is required
        if not knowledge_id:
            knowledge_id = full_config.get('id')
            if not knowledge_id:
                raise ValueError(f"Knowledge ID is required for knowledge base '{name}'")
        
        return OpenSearchKnowledgeBase(name, full_config, knowledge_id, self.cache)
    
    def get_supported_types(self) -> List[str]:
        """
        Get supported knowledge base types.
        
        Returns:
            List of supported types
        """
        return [
            'website',
            'sitemap',
            # Future loader types can be added here:
            # 'documents',
            # 'pdf',
            # 'directory',
            # 'database',
            # etc.
        ]