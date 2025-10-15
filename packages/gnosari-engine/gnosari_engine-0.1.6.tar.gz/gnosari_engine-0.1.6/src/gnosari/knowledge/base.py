"""
Base interfaces for knowledge management in Gnosari AI Teams.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from pydantic import BaseModel


@dataclass
class KnowledgeQuery:
    """Represents a query to a knowledge base."""
    query: str
    knowledge_base: str
    max_results: int = 5
    context: Optional[Dict[str, Any]] = None


@dataclass 
class KnowledgeResult:
    """Represents a result from a knowledge base query."""
    content: str
    source: str
    score: float
    metadata: Optional[Dict[str, Any]] = None


class KnowledgeConfig(BaseModel):
    """Configuration for a knowledge base."""
    name: str
    type: str
    data_sources: List[str]
    config: Optional[Dict[str, Any]] = None
    description: Optional[str] = None


class BaseKnowledgeBase(ABC):
    """
    Abstract base class for knowledge base implementations.
    """
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the knowledge base.
        
        Args:
            name: Name of the knowledge base
            config: Optional configuration dictionary
        """
        self.name = name
        self.config = config or {}
        self._initialized = False
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the knowledge base."""
        pass
    
    @abstractmethod
    async def add_data(self, data: str, source: str, metadata: Optional[Dict[str, Any]] = None) -> int:
        """
        Add data to the knowledge base.
        
        Args:
            data: Data content to add
            source: Source identifier for the data
            metadata: Optional metadata about the data
            
        Returns:
            Number of documents successfully added
        """
        pass
    
    @abstractmethod
    async def query(self, query: str, max_results: int = 5) -> List[KnowledgeResult]:
        """
        Query the knowledge base.
        
        Args:
            query: Query string
            max_results: Maximum number of results to return
            
        Returns:
            List of knowledge results
        """
        pass
    
    @abstractmethod
    async def delete_data(self, source: str) -> bool:
        """
        Delete data from the knowledge base.
        
        Args:
            source: Source identifier of data to delete
            
        Returns:
            True if data was deleted, False otherwise
        """
        pass
    
    async def cleanup(self) -> None:
        """Clean up resources used by the knowledge base."""
        pass
    
    def is_initialized(self) -> bool:
        """Check if the knowledge base is initialized."""
        return self._initialized


class KnowledgeProvider(ABC):
    """
    Abstract base class for knowledge providers that create knowledge bases.
    """
    
    @abstractmethod
    def create_knowledge_base(
        self, 
        name: str, 
        kb_type: str, 
        config: Optional[Dict[str, Any]] = None
    ) -> BaseKnowledgeBase:
        """
        Create a knowledge base.
        
        Args:
            name: Name of the knowledge base
            kb_type: Type of knowledge base to create
            config: Optional configuration
            
        Returns:
            Knowledge base instance
        """
        pass
    
    @abstractmethod
    def get_supported_types(self) -> List[str]:
        """
        Get list of supported knowledge base types.
        
        Returns:
            List of supported type names
        """
        pass