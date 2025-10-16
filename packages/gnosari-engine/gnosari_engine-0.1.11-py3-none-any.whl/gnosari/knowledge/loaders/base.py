"""
Base loader interface for OpenSearch knowledge bases.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseLoader(ABC):
    """Base class for OpenSearch data loaders."""
    
    @abstractmethod
    async def load_data(self, source: str, metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Load data from source and return list of documents.
        
        Args:
            source: Source identifier or URL
            metadata: Optional metadata to add to documents
            
        Returns:
            List of documents with 'text' field and optional metadata
        """
        pass