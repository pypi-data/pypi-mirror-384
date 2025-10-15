"""Base interface for learning storage implementations."""

from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseLearningStorage(ABC):
    """Abstract base class for learning storage implementations."""
    
    @abstractmethod
    def store_learning(self, session: Dict[str, Any], data: Dict[str, Any]) -> bool:
        """Store learning data.
        
        Args:
            session: Session information containing team and agent identifiers
            data: Learning data to store
            
        Returns:
            bool: True if learning was successfully stored, False otherwise
        """
        pass