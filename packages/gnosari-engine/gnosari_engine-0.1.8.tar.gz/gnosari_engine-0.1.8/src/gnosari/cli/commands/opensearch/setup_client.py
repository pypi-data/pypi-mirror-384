"""
OpenSearch Semantic Search Setup Client

This module provides the OpenSearchSemanticSetup class for setting up semantic search
using OpenSearch with OpenAI embeddings. It creates connectors, models, and indexes
for semantic search capabilities.

All configuration is handled through environment variables or direct parameters.

Requirements:
- OpenSearch instance (configurable host/port)
- OPENAI_API_KEY environment variable
- Required Python packages: opensearch-py, python-dotenv
"""

import os
import json
import time
import logging
from typing import Dict, Any, Optional

try:
    from opensearchpy import OpenSearch
except ImportError:
    OpenSearch = None

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv is optional
    pass


class OpenSearchSemanticSetup:
    """Setup semantic search with OpenAI embeddings in OpenSearch."""
    
    def __init__(self):
        """Initialize OpenSearch client with environment configuration."""
        if OpenSearch is None:
            raise ImportError("opensearch-py is required. Install with: pip install opensearch-py")
        
        # Load OpenSearch configuration
        self.opensearch_host = os.getenv('OPENSEARCH_HOST', 'localhost')
        self.opensearch_port = int(os.getenv('OPENSEARCH_PORT', '9200'))
        self.opensearch_use_ssl = os.getenv('OPENSEARCH_USE_SSL', 'false').lower() == 'true'
        self.opensearch_verify_certs = os.getenv('OPENSEARCH_VERIFY_CERTS', 'false').lower() == 'true'
        self.opensearch_username = os.getenv('OPENSEARCH_USERNAME')
        self.opensearch_password = os.getenv('OPENSEARCH_PASSWORD')
        self.opensearch_ca_certs = os.getenv('OPENSEARCH_CA_CERTS')
        
        # Build client configuration
        client_config = {
            'hosts': [{'host': self.opensearch_host, 'port': self.opensearch_port}],
            'http_compress': True,
            'use_ssl': self.opensearch_use_ssl,
            'verify_certs': self.opensearch_verify_certs,
            'ssl_assert_hostname': False,
            'ssl_show_warn': False,
            'timeout': int(os.getenv('OPENSEARCH_TIMEOUT', '30')),
        }
        
        # Add CA certificates if provided
        if self.opensearch_ca_certs:
            client_config['ca_certs'] = self.opensearch_ca_certs
        
        # Add authentication if provided
        if self.opensearch_username and self.opensearch_password:
            client_config['http_auth'] = (self.opensearch_username, self.opensearch_password)
        
        self.client = OpenSearch(**client_config)
        
        # Load OpenAI configuration
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        self.openai_model = os.getenv('OPENAI_EMBEDDING_MODEL', 'text-embedding-ada-002')
        self.openai_embedding_dimension = int(os.getenv('OPENAI_EMBEDDING_DIMENSION', '1536'))
        self.openai_api_url = os.getenv('OPENAI_API_URL', 'https://api.openai.com/v1/embeddings')
        
        # Load naming configuration
        self.connector_name = os.getenv('CONNECTOR_NAME', 'OpenAI embedding model connector')
        self.model_group_name = os.getenv('MODEL_GROUP_NAME', 'OpenAI_embedding_model_group')
        self.model_name = os.getenv('MODEL_NAME', 'OpenAI embedding model')
        self.pipeline_name = os.getenv('PIPELINE_NAME', 'openai_embedding_pipeline')
        self.index_name = os.getenv('INDEX_NAME', 'semantic_search_index')
        
        # Load vector search configuration
        self.vector_space_type = os.getenv('VECTOR_SPACE_TYPE', 'cosinesimil')
        self.vector_method = os.getenv('VECTOR_METHOD', 'hnsw')
        self.vector_ef_construction = int(os.getenv('VECTOR_EF_CONSTRUCTION', '512'))
        self.vector_m = int(os.getenv('VECTOR_M', '16'))
        self.search_k_value = int(os.getenv('SEARCH_K_VALUE', '10'))
        self.search_size = int(os.getenv('SEARCH_SIZE', '3'))
        
        # Load operational configuration
        self.task_timeout = int(os.getenv('TASK_TIMEOUT', '60'))
        self.task_poll_interval = int(os.getenv('TASK_POLL_INTERVAL', '2'))
        self.cleanup_on_failure = os.getenv('CLEANUP_ON_FAILURE', 'true').lower() == 'true'
        self.enable_sample_data = os.getenv('ENABLE_SAMPLE_DATA', 'true').lower() == 'true'
        self.enable_test_search = os.getenv('ENABLE_TEST_SEARCH', 'true').lower() == 'true'
        self.test_query = os.getenv('TEST_QUERY', 'search technology')
        self.force_recreate = os.getenv('FORCE_RECREATE', 'false').lower() == 'true'
        
        # Load hybrid search configuration
        self.enable_hybrid_search = os.getenv('ENABLE_HYBRID_SEARCH', 'true').lower() == 'true'
        self.search_pipeline_name = os.getenv('SEARCH_PIPELINE_NAME', 'nlp_search_pipeline')
        self.hybrid_normalization_technique = os.getenv('HYBRID_NORMALIZATION_TECHNIQUE', 'min_max')
        self.hybrid_combination_technique = os.getenv('HYBRID_COMBINATION_TECHNIQUE', 'arithmetic_mean')
        self.hybrid_keyword_weight = float(os.getenv('HYBRID_KEYWORD_WEIGHT', '0.3'))
        self.hybrid_semantic_weight = float(os.getenv('HYBRID_SEMANTIC_WEIGHT', '0.7'))
        
        # Load index configuration
        self.index_number_of_shards = int(os.getenv('INDEX_NUMBER_OF_SHARDS', '1'))
        self.index_number_of_replicas = int(os.getenv('INDEX_NUMBER_OF_REPLICAS', '1'))
        self.index_refresh_interval = os.getenv('INDEX_REFRESH_INTERVAL', '1s')
        
        # Store IDs for cleanup and reference
        self.connector_id: Optional[str] = None
        self.model_group_id: Optional[str] = None
        self.model_id: Optional[str] = None
        self.search_pipeline_created = False
        
        # Configure logging
        self.logger = logging.getLogger(__name__)
    
    def check_cluster_health(self) -> bool:
        """Check if OpenSearch cluster is healthy."""
        try:
            health = self.client.cluster.health()
            self.logger.info(f"Cluster health: {health['status']}")
            return health['status'] in ['green', 'yellow']
        except Exception as e:
            self.logger.error(f"Failed to check cluster health: {e}")
            return False
    
    def create_connector(self) -> str:
        """Create OpenAI embedding connector for OpenSearch."""
        self.logger.info("Creating OpenAI embedding connector...")
        
        connector_payload = {
            "name": self.connector_name,
            "description": f"Connector for {self.openai_model} model",
            "version": "1.0",
            "protocol": "http",
            "credential": {
                "openAI_key": self.openai_api_key
            },
            "parameters": {
                "model": self.openai_model
            },
            "actions": [
                {
                    "action_type": "predict",
                    "method": "POST",
                    "url": self.openai_api_url,
                    "headers": {
                        "Authorization": "Bearer ${credential.openAI_key}"
                    },
                    "request_body": "{ \"input\": ${parameters.input}, \"model\": \"${parameters.model}\" }",
                    "pre_process_function": "connector.pre_process.openai.embedding",
                    "post_process_function": "connector.post_process.openai.embedding"
                }
            ]
        }
        
        try:
            response = self.client.transport.perform_request(
                "POST",
                "/_plugins/_ml/connectors/_create",
                body=connector_payload
            )
            
            self.connector_id = response['connector_id']
            self.logger.info(f"Connector created successfully: {self.connector_id}")
            return self.connector_id
            
        except Exception as e:
            self.logger.error(f"Failed to create connector: {e}")
            raise
    
    def create_model_group(self) -> str:
        """Create model group for organizing models."""
        self.logger.info("Creating model group...")
        
        model_group_payload = {
            "name": self.model_group_name,
            "description": f"Model group for {self.openai_model} models"
        }
        
        try:
            response = self.client.transport.perform_request(
                "POST",
                "/_plugins/_ml/model_groups/_register",
                body=model_group_payload
            )
            
            self.model_group_id = response['model_group_id']
            self.logger.info(f"Model group created successfully: {self.model_group_id}")
            return self.model_group_id
            
        except Exception as e:
            self.logger.error(f"Failed to create model group: {e}")
            raise
    
    def register_model(self) -> str:
        """Register the OpenAI embedding model."""
        if not self.connector_id or not self.model_group_id:
            raise ValueError("Connector and model group must be created first")
        
        self.logger.info("Registering OpenAI embedding model...")
        
        model_payload = {
            "name": self.model_name,
            "function_name": "remote",
            "description": f"OpenAI {self.openai_model} model",
            "model_group_id": self.model_group_id,
            "connector_id": self.connector_id
        }
        
        try:
            response = self.client.transport.perform_request(
                "POST",
                "/_plugins/_ml/models/_register",
                body=model_payload
            )
            
            self.model_id = response['model_id']
            task_id = response['task_id']
            self.logger.info(f"Model registration initiated. Task ID: {task_id}, Model ID: {self.model_id}")
            
            # Wait for registration to complete
            self._wait_for_task(task_id)
            return self.model_id
            
        except Exception as e:
            self.logger.error(f"Failed to register model: {e}")
            raise
    
    def deploy_model(self) -> bool:
        """Deploy the registered model."""
        if not self.model_id:
            raise ValueError("Model must be registered first")
        
        self.logger.info("Deploying model...")
        
        try:
            response = self.client.transport.perform_request(
                "POST",
                f"/_plugins/_ml/models/{self.model_id}/_deploy"
            )
            
            task_id = response['task_id']
            self.logger.info(f"Model deployment initiated. Task ID: {task_id}")
            
            # Wait for deployment to complete
            success = self._wait_for_task(task_id)
            if success:
                self.logger.info("Model deployed successfully")
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to deploy model: {e}")
            raise
    
    def test_model(self) -> bool:
        """Test the deployed model with sample data."""
        if not self.model_id:
            raise ValueError("Model must be deployed first")
        
        self.logger.info("Testing model with sample data...")
        
        test_input = os.getenv('TEST_INPUT', '["hello world", "semantic search test"]')
        try:
            test_data = json.loads(test_input)
        except json.JSONDecodeError:
            test_data = ["hello world", "semantic search test"]
        
        test_payload = {
            "parameters": {
                "input": test_data
            }
        }
        
        try:
            response = self.client.transport.perform_request(
                "POST",
                f"/_plugins/_ml/models/{self.model_id}/_predict",
                body=test_payload
            )
            
            if response.get('inference_results'):
                self.logger.info("Model test successful - embeddings generated")
                return True
            else:
                self.logger.error("Model test failed - no embeddings generated")
                return False
                
        except Exception as e:
            self.logger.error(f"Model test failed: {e}")
            return False
    
    def create_ingest_pipeline(self) -> bool:
        """Create ingest pipeline for text embedding."""
        if not self.model_id:
            raise ValueError("Model must be deployed first")
        
        self.logger.info(f"Creating ingest pipeline: {self.pipeline_name}")
        
        pipeline_payload = {
            "description": f"Text embedding pipeline using {self.openai_model}",
            "processors": [
                {
                    "text_embedding": {
                        "model_id": self.model_id,
                        "field_map": {
                            "text": "text_embedding"
                        }
                    }
                }
            ]
        }
        
        try:
            # Delete pipeline if it exists and force recreate is enabled
            if self.force_recreate:
                try:
                    self.client.ingest.delete_pipeline(id=self.pipeline_name)
                    self.logger.info(f"Deleted existing pipeline: {self.pipeline_name}")
                except:
                    pass
            
            response = self.client.ingest.put_pipeline(
                id=self.pipeline_name,
                body=pipeline_payload
            )
            
            self.logger.info("Ingest pipeline created successfully")
            return response.get('acknowledged', False)
            
        except Exception as e:
            self.logger.error(f"Failed to create ingest pipeline: {e}")
            return False
    
    def create_search_pipeline(self) -> bool:
        """Create search pipeline for hybrid search."""
        if not self.enable_hybrid_search:
            self.logger.info("Hybrid search disabled, skipping search pipeline creation")
            return True
            
        self.logger.info(f"Creating search pipeline: {self.search_pipeline_name}")
        
        pipeline_payload = {
            "description": f"Hybrid search pipeline using {self.hybrid_normalization_technique} normalization and {self.hybrid_combination_technique} combination",
            "phase_results_processors": [
                {
                    "normalization-processor": {
                        "normalization": {
                            "technique": self.hybrid_normalization_technique
                        },
                        "combination": {
                            "technique": self.hybrid_combination_technique,
                            "parameters": {
                                "weights": [
                                    self.hybrid_keyword_weight,
                                    self.hybrid_semantic_weight
                                ]
                            }
                        }
                    }
                }
            ]
        }
        
        try:
            # Delete search pipeline if it exists and force recreate is enabled
            if self.force_recreate:
                try:
                    self.client.transport.perform_request(
                        "DELETE",
                        f"/_search/pipeline/{self.search_pipeline_name}"
                    )
                    self.logger.info(f"Deleted existing search pipeline: {self.search_pipeline_name}")
                except:
                    pass
            
            response = self.client.transport.perform_request(
                "PUT",
                f"/_search/pipeline/{self.search_pipeline_name}",
                body=pipeline_payload
            )
            
            self.search_pipeline_created = True
            self.logger.info("Search pipeline created successfully")
            return response.get('acknowledged', False)
            
        except Exception as e:
            self.logger.error(f"Failed to create search pipeline: {e}")
            return False
    
    def create_vector_index(self) -> bool:
        """Create vector index for semantic search."""
        self.logger.info(f"Creating vector index: {self.index_name}")
        
        index_payload = {
            "settings": {
                "index": {
                    "knn.space_type": self.vector_space_type,
                    "default_pipeline": self.pipeline_name,
                    "knn": True,
                    "number_of_shards": self.index_number_of_shards,
                    "number_of_replicas": self.index_number_of_replicas,
                    "refresh_interval": self.index_refresh_interval
                },
                "knn": {
                    "algo_param": {
                        "ef_search": self.search_k_value
                    }
                }
            },
            "mappings": {
                "properties": {
                    "text": {
                        "type": "text"
                    },
                    "text_embedding": {
                        "type": "knn_vector",
                        "dimension": self.openai_embedding_dimension,
                        "method": {
                            "name": self.vector_method,
                            "space_type": self.vector_space_type,
                            "engine": "nmslib",
                            "parameters": {
                                "ef_construction": self.vector_ef_construction,
                                "m": self.vector_m
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
        
        try:
            # Delete index if it exists and force recreate is enabled
            if self.client.indices.exists(index=self.index_name):
                if self.force_recreate:
                    self.client.indices.delete(index=self.index_name)
                    self.logger.info(f"Deleted existing index: {self.index_name}")
                else:
                    self.logger.info(f"Index {self.index_name} already exists, skipping creation")
                    return True
            
            response = self.client.indices.create(
                index=self.index_name,
                body=index_payload
            )
            
            self.logger.info("Vector index created successfully")
            return response.get('acknowledged', False)
            
        except Exception as e:
            self.logger.error(f"Failed to create vector index: {e}")
            return False
    
    def ingest_sample_data(self) -> bool:
        """Ingest sample documents for testing."""
        if not self.enable_sample_data:
            self.logger.info("Sample data ingestion disabled")
            return True
            
        self.logger.info("Ingesting sample data...")
        
        # Load sample data from environment or use defaults
        sample_data_env = os.getenv('SAMPLE_DATA')
        if sample_data_env:
            try:
                sample_docs = json.loads(sample_data_env)
            except json.JSONDecodeError:
                self.logger.warning("Invalid SAMPLE_DATA JSON, using defaults")
                sample_docs = self._get_default_sample_data()
        else:
            sample_docs = self._get_default_sample_data()
        
        try:
            for i, doc in enumerate(sample_docs, 1):
                # Add timestamp if not present
                if 'timestamp' not in doc:
                    doc['timestamp'] = time.strftime('%Y-%m-%dT%H:%M:%S')
                
                response = self.client.index(
                    index=self.index_name,
                    id=f"sample_{i}",
                    body=doc
                )
                self.logger.info(f"Indexed document {i}")
            
            # Refresh index to make documents searchable
            self.client.indices.refresh(index=self.index_name)
            self.logger.info("Sample data ingested successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to ingest sample data: {e}")
            return False
    
    def test_semantic_search(self, query: str = None) -> Dict[str, Any]:
        """Test semantic search with a sample query."""
        if not self.enable_test_search:
            self.logger.info("Test search disabled")
            return {}
            
        if query is None:
            query = self.test_query
            
        self.logger.info(f"Testing semantic search with query: '{query}'")
        
        search_payload = {
            "query": {
                "neural": {
                    "text_embedding": {
                        "query_text": query,
                        "model_id": self.model_id,
                        "k": self.search_k_value
                    }
                }
            },
            "size": self.search_size,
            "_source": ["text", "metadata", "timestamp"]
        }
        
        try:
            response = self.client.search(
                index=self.index_name,
                body=search_payload
            )
            
            hits = response.get('hits', {}).get('hits', [])
            self.logger.info(f"Found {len(hits)} results")
            
            for i, hit in enumerate(hits, 1):
                score = hit['_score']
                text = hit['_source']['text']
                self.logger.info(f"Result {i} (score: {score:.4f}): {text}")
            
            return response
            
        except Exception as e:
            self.logger.error(f"Semantic search test failed: {e}")
            return {}
    
    def test_hybrid_search(self, query: str = None) -> Dict[str, Any]:
        """Test hybrid search combining keyword and semantic search."""
        if not self.enable_hybrid_search or not self.enable_test_search:
            self.logger.info("Hybrid search or test search disabled")
            return {}
            
        if query is None:
            query = self.test_query
            
        self.logger.info(f"Testing hybrid search with query: '{query}'")
        
        search_payload = {
            "_source": {
                "exclude": ["text_embedding"]
            },
            "query": {
                "hybrid": {
                    "queries": [
                        {
                            "match": {
                                "text": {
                                    "query": query
                                }
                            }
                        },
                        {
                            "neural": {
                                "text_embedding": {
                                    "query_text": query,
                                    "model_id": self.model_id,
                                    "k": self.search_k_value
                                }
                            }
                        }
                    ]
                }
            },
            "size": self.search_size
        }
        
        try:
            response = self.client.search(
                index=self.index_name,
                body=search_payload,
                params={"search_pipeline": self.search_pipeline_name}
            )
            
            hits = response.get('hits', {}).get('hits', [])
            self.logger.info(f"Hybrid search found {len(hits)} results")
            
            for i, hit in enumerate(hits, 1):
                score = hit['_score']
                text = hit['_source']['text']
                self.logger.info(f"Hybrid result {i} (score: {score:.4f}): {text}")
            
            return response
            
        except Exception as e:
            self.logger.error(f"Hybrid search test failed: {e}")
            return {}
    
    def _wait_for_task(self, task_id: str, timeout: int = None) -> bool:
        """Wait for a task to complete."""
        if timeout is None:
            timeout = self.task_timeout
            
        self.logger.info(f"Waiting for task {task_id} to complete...")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = self.client.transport.perform_request(
                    "GET",
                    f"/_plugins/_ml/tasks/{task_id}"
                )
                
                state = response.get('state', '')
                if state == 'COMPLETED':
                    self.logger.info(f"Task {task_id} completed successfully")
                    return True
                elif state == 'FAILED':
                    error = response.get('error', 'Unknown error')
                    self.logger.error(f"Task {task_id} failed: {error}")
                    return False
                
                time.sleep(self.task_poll_interval)
                
            except Exception as e:
                self.logger.error(f"Error checking task status: {e}")
                time.sleep(self.task_poll_interval)
        
        self.logger.error(f"Task {task_id} timed out after {timeout} seconds")
        return False
    
    def cleanup(self):
        """Clean up created resources."""
        self.logger.info("Cleaning up resources...")
        
        try:
            # Delete index
            if self.index_name and self.client.indices.exists(index=self.index_name):
                self.client.indices.delete(index=self.index_name)
                self.logger.info(f"Deleted index: {self.index_name}")
            
            # Delete ingest pipeline
            if self.pipeline_name:
                try:
                    self.client.ingest.delete_pipeline(id=self.pipeline_name)
                    self.logger.info(f"Deleted ingest pipeline: {self.pipeline_name}")
                except:
                    pass
            
            # Delete search pipeline
            if self.search_pipeline_created and self.search_pipeline_name:
                try:
                    self.client.transport.perform_request(
                        "DELETE",
                        f"/_search/pipeline/{self.search_pipeline_name}"
                    )
                    self.logger.info(f"Deleted search pipeline: {self.search_pipeline_name}")
                except:
                    pass
            
            # Undeploy model
            if self.model_id:
                try:
                    self.client.transport.perform_request(
                        "POST",
                        f"/_plugins/_ml/models/{self.model_id}/_undeploy"
                    )
                    self.logger.info(f"Undeployed model: {self.model_id}")
                except:
                    pass
            
        except Exception as e:
            self.logger.error(f"Cleanup error: {e}")
    
    def setup_complete_pipeline(self) -> bool:
        """Set up the complete semantic search pipeline."""
        self.logger.info("Starting complete semantic search setup...")
        
        try:
            # Print configuration
            self.print_configuration()
            
            # Check cluster health
            if not self.check_cluster_health():
                raise Exception("OpenSearch cluster is not healthy")
            
            # Create connector
            self.create_connector()
            
            # Create model group
            self.create_model_group()
            
            # Register and deploy model
            self.register_model()
            self.deploy_model()
            
            # Test model
            if not self.test_model():
                raise Exception("Model test failed")
            
            # Create pipelines and index
            self.create_ingest_pipeline()
            self.create_search_pipeline()
            self.create_vector_index()
            
            # Ingest sample data
            self.ingest_sample_data()
            
            # Test semantic search
            self.test_semantic_search()
            
            # Test hybrid search
            self.test_hybrid_search()
            
            self.logger.info("Semantic search setup completed successfully!")
            self.logger.info(f"Model ID: {self.model_id}")
            self.logger.info(f"Index name: {self.index_name}")
            self.logger.info(f"Ingest Pipeline name: {self.pipeline_name}")
            if self.enable_hybrid_search:
                self.logger.info(f"Search Pipeline name: {self.search_pipeline_name}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Setup failed: {e}")
            if self.cleanup_on_failure:
                self.cleanup()
            return False
    
    def _get_default_sample_data(self) -> list:
        """Get default sample data for testing."""
        return [
            {
                "text": "OpenSearch is a powerful search and analytics engine",
                "metadata": {"category": "technology", "type": "definition"}
            },
            {
                "text": "Machine learning models can generate embeddings for text",
                "metadata": {"category": "ai", "type": "concept"}
            },
            {
                "text": "Semantic search finds documents based on meaning rather than exact matches",
                "metadata": {"category": "search", "type": "explanation"}
            },
            {
                "text": "Vector databases store high-dimensional embeddings efficiently",
                "metadata": {"category": "database", "type": "concept"}
            },
            {
                "text": "Natural language processing enables computers to understand human language",
                "metadata": {"category": "ai", "type": "definition"}
            },
            {
                "text": "Embeddings capture semantic meaning in high-dimensional space",
                "metadata": {"category": "ai", "type": "concept"}
            }
        ]
    
    def print_configuration(self):
        """Print current configuration."""
        self.logger.info("=" * 60)
        self.logger.info("OPENSEARCH SEMANTIC SEARCH CONFIGURATION")
        self.logger.info("=" * 60)
        self.logger.info(f"OpenSearch: {self.opensearch_host}:{self.opensearch_port} (SSL: {self.opensearch_use_ssl})")
        self.logger.info(f"OpenAI Model: {self.openai_model} (Dimension: {self.openai_embedding_dimension})")
        self.logger.info(f"Index Name: {self.index_name}")
        self.logger.info(f"Pipeline Name: {self.pipeline_name}")
        self.logger.info(f"Vector Method: {self.vector_method} ({self.vector_space_type})")
        self.logger.info(f"Vector Parameters: ef_construction={self.vector_ef_construction}, m={self.vector_m}")
        self.logger.info(f"Search Parameters: k={self.search_k_value}, size={self.search_size}")
        self.logger.info(f"Task Timeout: {self.task_timeout}s")
        self.logger.info(f"Sample Data: {self.enable_sample_data}")
        self.logger.info(f"Test Search: {self.enable_test_search}")
        self.logger.info(f"Force Recreate: {self.force_recreate}")
        self.logger.info(f"Cleanup on Failure: {self.cleanup_on_failure}")
        self.logger.info(f"Hybrid Search: {self.enable_hybrid_search}")
        if self.enable_hybrid_search:
            self.logger.info(f"  - Search Pipeline: {self.search_pipeline_name}")
            self.logger.info(f"  - Normalization: {self.hybrid_normalization_technique}")
            self.logger.info(f"  - Combination: {self.hybrid_combination_technique}")
            self.logger.info(f"  - Weights: keyword={self.hybrid_keyword_weight}, semantic={self.hybrid_semantic_weight}")
        self.logger.info("=" * 60)