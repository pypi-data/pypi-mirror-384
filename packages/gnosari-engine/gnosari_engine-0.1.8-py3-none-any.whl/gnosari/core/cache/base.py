"""
Base interfaces and abstractions for the generic cache system.

This module defines the core contracts that all cache implementations must follow,
enabling extensibility and interchangeability of components.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, TypeVar, Protocol, runtime_checkable
from dataclasses import dataclass


# Type variable for cacheable items
T = TypeVar('T')


@runtime_checkable
class Cacheable(Protocol):
    """
    Protocol for items that can be cached.
    
    Any object implementing this protocol can be stored in the cache system.
    This follows the Interface Segregation Principle by only requiring
    what's necessary for caching.
    """
    
    def get_cache_key(self) -> str:
        """
        Get the unique cache key for this item.
        
        Returns:
            Unique string identifier for cache storage
        """
        ...
    
    def get_cache_data(self) -> Dict[str, Any]:
        """
        Get the data that should be cached for this item.
        
        Returns:
            Dictionary containing all data needed to restore this item
        """
        ...


@dataclass
class CacheableItem:
    """
    Simple implementation of Cacheable for basic use cases.
    
    This provides a concrete implementation that can be used directly
    or extended for more complex caching scenarios.
    """
    key: str
    data: Dict[str, Any]
    
    def get_cache_key(self) -> str:
        """Get the cache key."""
        return self.key
    
    def get_cache_data(self) -> Dict[str, Any]:
        """Get the cache data."""
        return self.data.copy()


class HashStrategy(ABC):
    """
    Abstract base class for different hashing strategies.
    
    This allows different hashing algorithms to be plugged in
    following the Open/Closed Principle.
    """
    
    @abstractmethod
    def compute_hash(self, data: Dict[str, Any]) -> str:
        """
        Compute a hash for the given data.
        
        Args:
            data: Data to hash
            
        Returns:
            Hash string that uniquely identifies the data
        """
        pass
    
    @abstractmethod
    def get_algorithm_name(self) -> str:
        """
        Get the name of the hashing algorithm.
        
        Returns:
            Human-readable name of the algorithm
        """
        pass


class CacheStorage(ABC, Generic[T]):
    """
    Abstract base class for cache storage backends.
    
    This enables different storage mechanisms (JSON files, databases, etc.)
    to be implemented following the Dependency Inversion Principle.
    """
    
    @abstractmethod
    def load(self) -> Dict[str, T]:
        """
        Load all cache entries from storage.
        
        Returns:
            Dictionary mapping cache keys to cache entries
        """
        pass
    
    @abstractmethod
    def save(self, cache_data: Dict[str, T]) -> None:
        """
        Save cache entries to storage.
        
        Args:
            cache_data: Dictionary of cache entries to save
        """
        pass
    
    @abstractmethod
    def exists(self) -> bool:
        """
        Check if the cache storage exists.
        
        Returns:
            True if storage exists, False otherwise
        """
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """Clear all cache data from storage."""
        pass


class CacheValidator(ABC):
    """
    Abstract base class for cache validation strategies.
    
    This allows different validation logic to be implemented
    for determining if cached items are still valid.
    """
    
    @abstractmethod
    def is_valid(self, cache_entry: 'CacheEntry', current_data: Dict[str, Any]) -> bool:
        """
        Check if a cache entry is still valid.
        
        Args:
            cache_entry: The cached entry to validate
            current_data: Current data to compare against
            
        Returns:
            True if the cache entry is still valid
        """
        pass
    
    @abstractmethod
    def get_validation_strategy_name(self) -> str:
        """
        Get the name of the validation strategy.
        
        Returns:
            Human-readable name of the validation strategy
        """
        pass