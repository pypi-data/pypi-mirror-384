"""
Generic cache system for Gnosari AI Teams.

This package provides a flexible, type-safe caching system that can be used
across all modules to cache configurations, computations, and other data.

The system follows SOLID principles:
- Single Responsibility: Each class has one clear purpose
- Open/Closed: Extensible without modification via interfaces
- Liskov Substitution: Implementations are interchangeable
- Interface Segregation: Clean, focused interfaces
- Dependency Inversion: Depends on abstractions, not concretions
"""

from .base import Cacheable, CacheableItem, HashStrategy
from .entry import CacheEntry, CacheStatus
from .manager import CacheManager, CacheConfig
from .hashers import ConfigHasher, ContentHasher, MD5Hasher, CombinedHasher

__all__ = [
    # Core interfaces
    'Cacheable',
    'CacheableItem', 
    'HashStrategy',
    
    # Cache entry system
    'CacheEntry',
    'CacheStatus',
    
    # Cache manager
    'CacheManager',
    'CacheConfig',
    
    # Hash strategies
    'ConfigHasher',
    'ContentHasher',
    'MD5Hasher',
    'CombinedHasher',
]