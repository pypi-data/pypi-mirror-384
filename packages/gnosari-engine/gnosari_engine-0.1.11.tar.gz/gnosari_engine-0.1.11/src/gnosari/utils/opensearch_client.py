"""
OpenSearch client for indexing events in Gnosari.
"""

import json
import logging
import os
from typing import Dict, Any, Optional
from datetime import datetime
from opensearchpy import OpenSearch, RequestsHttpConnection
from opensearchpy.exceptions import OpenSearchException

from ..utils.logging import get_logger

logger = get_logger(__name__)


class OpenSearchClient:
    """OpenSearch client for event indexing."""
    
    def __init__(self, 
                 host: str = "localhost", 
                 port: int = 9200,
                 use_ssl: bool = False,
                 verify_certs: bool = False,
                 index_prefix: str = "gnosari-events"):
        """Initialize OpenSearch client.
        
        Args:
            host: OpenSearch host
            port: OpenSearch port  
            use_ssl: Whether to use SSL
            verify_certs: Whether to verify SSL certificates
            index_prefix: Index prefix for event indices
        """
        self.host = host
        self.port = port
        self.use_ssl = use_ssl
        self.verify_certs = verify_certs
        self.index_prefix = index_prefix
        
        # Initialize client
        self.client = OpenSearch(
            hosts=[{"host": host, "port": port}],
            http_compress=True,
            use_ssl=use_ssl,
            verify_certs=verify_certs,
            ssl_assert_hostname=False,
            ssl_show_warn=False,
            connection_class=RequestsHttpConnection,
            timeout=30,
            max_retries=1,
            retry_on_timeout=True
        )
        
        # Test connection
        self._test_connection()
    
    def _test_connection(self) -> bool:
        """Test OpenSearch connection.
        
        Returns:
            bool: True if connection successful
        """
        try:
            info = self.client.info()
            logger.info(f"Connected to OpenSearch: {info.get('version', {}).get('number', 'unknown')}")
            return True
        except Exception as e:
            logger.warning(f"OpenSearch connection failed: {e}")
            return False
    
    def _get_index_name(self, event_type: str) -> str:
        """Get index name for event type.
        
        Args:
            event_type: Event type
            
        Returns:
            str: Index name
        """
        # Use date-based index pattern for time-series data
        date_suffix = datetime.utcnow().strftime("%Y-%m")
        return f"{self.index_prefix}-{date_suffix}"
    
    def _ensure_index_exists(self, index_name: str) -> None:
        """Ensure index exists with proper mapping.
        
        Args:
            index_name: Index name
        """
        try:
            if not self.client.indices.exists(index=index_name):
                # Define mapping for events
                mapping = {
                    "mappings": {
                        "properties": {
                            "event_id": {"type": "keyword"},
                            "event_type": {"type": "keyword"},
                            "source": {"type": "keyword"},
                            "priority": {"type": "integer"},
                            "timestamp": {"type": "date"},
                            "processed_at": {"type": "date"},
                            "status": {"type": "keyword"},
                            "data": {
                                "type": "object",
                                "enabled": True
                            },
                            "metadata": {
                                "type": "object", 
                                "enabled": True
                            },
                            "context": {
                                "type": "object",
                                "enabled": True
                            },
                            "session": {
                                "type": "object",
                                "enabled": True
                            },
                            "processing_result": {
                                "type": "object",
                                "enabled": True
                            },
                            "error": {"type": "text"},
                            "message": {"type": "text"}
                        }
                    },
                    "settings": {
                        "number_of_shards": 1,
                        "number_of_replicas": 0
                    }
                }
                
                self.client.indices.create(index=index_name, body=mapping)
                logger.info(f"Created OpenSearch index: {index_name}")
        except Exception as e:
            logger.error(f"Failed to create index {index_name}: {e}")
    
    def index_event(self, event_data: Dict[str, Any], processing_result: Optional[Dict[str, Any]] = None) -> bool:
        """Index an event in OpenSearch.
        
        Args:
            event_data: Event data to index
            processing_result: Optional processing result to include
            
        Returns:
            bool: True if indexing successful
        """
        try:
            event_type = event_data.get("event_type", "unknown")
            index_name = self._get_index_name(event_type)
            
            # Ensure index exists
            self._ensure_index_exists(index_name)
            
            # Prepare document for indexing
            doc = {
                "event_id": event_data.get("event_id"),
                "event_type": event_type,
                "source": event_data.get("source"),
                "priority": event_data.get("priority", 5),
                "timestamp": event_data.get("timestamp"),
                "processed_at": datetime.utcnow().isoformat(),
                "data": event_data.get("data", {}),
                "metadata": event_data.get("metadata", {}),
                "context": event_data.get("context", {}),
                "session": event_data.get("session", {})
            }
            
            # Add processing result if provided
            if processing_result:
                doc["processing_result"] = processing_result
                doc["status"] = processing_result.get("status", "unknown")
                if "error" in processing_result:
                    doc["error"] = processing_result["error"]
                if "message" in processing_result:
                    doc["message"] = processing_result["message"]
            else:
                doc["status"] = "processed"
            
            # Index document
            response = self.client.index(
                index=index_name,
                id=event_data.get("event_id"),
                body=doc,
                refresh=False  # Don't force refresh for performance
            )
            
            logger.debug(f"Indexed event {event_data.get('event_id')} in {index_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to index event {event_data.get('event_id', 'unknown')}: {e}")
            return False
    
    def search_events(self, 
                     event_type: Optional[str] = None,
                     source: Optional[str] = None,
                     status: Optional[str] = None,
                     start_time: Optional[datetime] = None,
                     end_time: Optional[datetime] = None,
                     size: int = 100) -> Dict[str, Any]:
        """Search events in OpenSearch.
        
        Args:
            event_type: Filter by event type
            source: Filter by source
            status: Filter by status
            start_time: Start time filter
            end_time: End time filter
            size: Maximum number of results
            
        Returns:
            Dict: Search results
        """
        try:
            # Build query
            query = {"bool": {"must": []}}
            
            if event_type:
                query["bool"]["must"].append({"term": {"event_type": event_type}})
            
            if source:
                query["bool"]["must"].append({"term": {"source": source}})
                
            if status:
                query["bool"]["must"].append({"term": {"status": status}})
            
            if start_time or end_time:
                time_range = {}
                if start_time:
                    time_range["gte"] = start_time.isoformat()
                if end_time:
                    time_range["lte"] = end_time.isoformat()
                query["bool"]["must"].append({"range": {"timestamp": time_range}})
            
            # Search across all event indices
            index_pattern = f"{self.index_prefix}-*"
            
            body = {
                "query": query,
                "sort": [{"timestamp": {"order": "desc"}}],
                "size": size
            }
            
            response = self.client.search(index=index_pattern, body=body)
            return response
            
        except Exception as e:
            logger.error(f"Failed to search events: {e}")
            return {"hits": {"hits": []}}


# Global client instance
_opensearch_client: Optional[OpenSearchClient] = None


def get_opensearch_client() -> Optional[OpenSearchClient]:
    """Get or create OpenSearch client instance.
    
    Returns:
        OpenSearchClient: Client instance or None if initialization fails
    """
    global _opensearch_client
    
    if _opensearch_client is None:
        try:
            # Get configuration from environment
            opensearch_url = os.getenv("OPENSEARCH_URL", "localhost:9200")
            
            # Parse URL to extract host and port
            if "://" in opensearch_url:
                # Full URL format: http://opensearch:9200
                from urllib.parse import urlparse
                parsed = urlparse(opensearch_url)
                host = parsed.hostname or "localhost"
                port = parsed.port or 9200
                use_ssl = parsed.scheme == "https"
            else:
                # Host:port format: opensearch:9200
                if ":" in opensearch_url:
                    host, port_str = opensearch_url.split(":", 1)
                    port = int(port_str)
                else:
                    host = opensearch_url
                    port = 9200
                use_ssl = os.getenv("OPENSEARCH_SSL", "false").lower() == "true"
            
            verify_certs = os.getenv("OPENSEARCH_VERIFY_CERTS", "false").lower() == "true"
            index_prefix = os.getenv("OPENSEARCH_INDEX_PREFIX", "gnosari-events")
            
            _opensearch_client = OpenSearchClient(
                host=host,
                port=port,
                use_ssl=use_ssl,
                verify_certs=verify_certs,
                index_prefix=index_prefix
            )
            
        except Exception as e:
            logger.warning(f"Failed to initialize OpenSearch client: {e}")
            _opensearch_client = None
    
    return _opensearch_client


def index_event_document(event_data: Dict[str, Any], processing_result: Optional[Dict[str, Any]] = None) -> bool:
    """Index an event document in OpenSearch.
    
    Args:
        event_data: Event data to index
        processing_result: Optional processing result
        
    Returns:
        bool: True if successful
    """
    client = get_opensearch_client()
    if client:
        return client.index_event(event_data, processing_result)
    return False