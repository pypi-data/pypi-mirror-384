"""
Generic cache manager implementation.

This module provides the main CacheManager class that orchestrates all
cache operations following SOLID principles and providing type safety.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Generic, List, Optional, Set, TypeVar, Union
from dataclasses import dataclass

from .base import Cacheable, HashStrategy, CacheStorage, CacheValidator
from .entry import CacheEntry, CacheStatus
from .hashers import ConfigHasher


# Type variable for cached items
T = TypeVar('T')


@dataclass
class CacheConfig:
    """
    Configuration for cache manager instances.
    
    This follows the Single Responsibility Principle by encapsulating
    all configuration concerns in one place.
    """
    cache_dir: str
    cache_name: str
    hash_strategy: HashStrategy
    max_entries: Optional[int] = None
    default_ttl_hours: Optional[int] = None
    auto_cleanup: bool = True
    
    @property
    def cache_file_path(self) -> Path:
        """Get the full path to the cache file."""
        return Path(self.cache_dir) / f"{self.cache_name}.json"


class JSONCacheStorage(CacheStorage[CacheEntry]):
    """
    JSON file-based cache storage implementation.
    
    This provides a concrete storage backend using JSON files,
    following the Dependency Inversion Principle.
    """
    
    def __init__(self, file_path: Path):
        """
        Initialize JSON cache storage.
        
        Args:
            file_path: Path to the JSON cache file
        """
        self.file_path = file_path
        self.logger = logging.getLogger(__name__)
    
    def load(self) -> Dict[str, CacheEntry]:
        """Load cache entries from JSON file."""
        try:
            if self.file_path.exists():
                with open(self.file_path, 'r') as f:
                    cache_data = json.load(f)
                
                # Convert dictionaries back to CacheEntry objects
                entries = {}
                for key, entry_dict in cache_data.items():
                    try:
                        entries[key] = CacheEntry.from_dict(entry_dict)
                    except Exception as e:
                        self.logger.warning(f"Failed to load cache entry '{key}': {e}")
                
                self.logger.debug(f"Loaded {len(entries)} cache entries from {self.file_path}")
                return entries
            else:
                self.logger.debug(f"No cache file found at {self.file_path}, starting fresh")
                return {}
        except Exception as e:
            self.logger.error(f"Failed to load cache from {self.file_path}: {e}")
            return {}
    
    def save(self, cache_data: Dict[str, CacheEntry]) -> None:
        """Save cache entries to JSON file."""
        try:
            # Ensure directory exists
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert CacheEntry objects to dictionaries
            serializable_data = {
                key: entry.to_dict() 
                for key, entry in cache_data.items()
            }
            
            with open(self.file_path, 'w') as f:
                json.dump(serializable_data, f, indent=2)
            
            self.logger.debug(f"Saved {len(cache_data)} cache entries to {self.file_path}")
        except Exception as e:
            self.logger.error(f"Failed to save cache to {self.file_path}: {e}")
    
    def exists(self) -> bool:
        """Check if the cache file exists."""
        return self.file_path.exists()
    
    def clear(self) -> None:
        """Clear the cache file."""
        try:
            if self.file_path.exists():
                self.file_path.unlink()
                self.logger.debug(f"Cleared cache file {self.file_path}")
        except Exception as e:
            self.logger.error(f"Failed to clear cache file {self.file_path}: {e}")


class HashCacheValidator(CacheValidator):
    """
    Hash-based cache validation strategy.
    
    This validator uses content hashes to determine if cached items are still valid.
    """
    
    def __init__(self, hash_strategy: HashStrategy):
        """
        Initialize with a hash strategy.
        
        Args:
            hash_strategy: Strategy to use for computing hashes
        """
        self.hash_strategy = hash_strategy
    
    def is_valid(self, cache_entry: CacheEntry, current_data: Dict[str, Any]) -> bool:
        """Check if cache entry is valid by comparing hashes."""
        if cache_entry.status != CacheStatus.LOADED:
            return False
        
        if cache_entry.is_expired():
            return False
        
        current_hash = self.hash_strategy.compute_hash(current_data)
        return cache_entry.content_hash == current_hash
    
    def get_validation_strategy_name(self) -> str:
        """Get the validation strategy name."""
        return f"Hash-{self.hash_strategy.get_algorithm_name()}"


class CacheManager(Generic[T]):
    """
    Generic cache manager for any type of cacheable items.
    
    This class provides a high-level interface for caching with support for:
    - Type safety through generics
    - Pluggable hash strategies
    - Flexible storage backends
    - Automatic validation and cleanup
    - Rich metadata tracking
    """
    
    def __init__(
        self, 
        config: CacheConfig,
        storage: Optional[CacheStorage[CacheEntry]] = None,
        validator: Optional[CacheValidator] = None
    ):
        """
        Initialize the cache manager.
        
        Args:
            config: Cache configuration
            storage: Storage backend (defaults to JSON storage)
            validator: Cache validator (defaults to hash validator)
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize storage backend
        if storage is None:
            storage = JSONCacheStorage(config.cache_file_path)
        self.storage = storage
        
        # Initialize validator
        if validator is None:
            validator = HashCacheValidator(config.hash_strategy)
        self.validator = validator
        
        # In-memory cache for faster access
        self._cache: Dict[str, CacheEntry] = {}
        
        # Load existing cache
        self._load_cache()
    
    def _load_cache(self) -> None:
        """Load cache from storage."""
        try:
            self._cache = self.storage.load()
            
            # Auto cleanup if enabled
            if self.config.auto_cleanup:
                self._cleanup_invalid_entries()
            
            self.logger.debug(f"Cache manager initialized with {len(self._cache)} entries")
        except Exception as e:
            self.logger.error(f"Failed to load cache: {e}")
            self._cache = {}
    
    def _save_cache(self) -> None:
        """Save cache to storage."""
        try:
            self.storage.save(self._cache)
        except Exception as e:
            self.logger.error(f"Failed to save cache: {e}")
    
    def _cleanup_invalid_entries(self) -> None:
        """Clean up invalid and expired entries."""
        invalid_keys = []
        
        for key, entry in self._cache.items():
            if entry.is_expired():
                entry.update_status(CacheStatus.EXPIRED)
                invalid_keys.append(key)
            elif entry.status in (CacheStatus.FAILED, CacheStatus.INVALID):
                invalid_keys.append(key)
        
        for key in invalid_keys:
            del self._cache[key]
        
        if invalid_keys:
            self._save_cache()
            self.logger.info(f"Cleaned up {len(invalid_keys)} invalid cache entries")
    
    def _enforce_max_entries(self) -> None:
        """Enforce maximum number of cache entries."""
        if not self.config.max_entries:
            return
        
        if len(self._cache) <= self.config.max_entries:
            return
        
        # Remove least recently accessed entries
        sorted_entries = sorted(
            self._cache.items(),
            key=lambda x: x[1].last_accessed
        )
        
        entries_to_remove = len(self._cache) - self.config.max_entries
        for i in range(entries_to_remove):
            key = sorted_entries[i][0]
            del self._cache[key]
        
        self._save_cache()
        self.logger.info(f"Removed {entries_to_remove} entries to enforce max_entries limit")
    
    def is_cached(self, cache_key: str, current_data: Dict[str, Any]) -> bool:
        """
        Check if an item is cached and valid.
        
        Args:
            cache_key: Unique identifier for the cached item
            current_data: Current data to validate against
            
        Returns:
            True if item is cached and valid
        """
        entry = self._cache.get(cache_key)
        if not entry:
            return False
        
        is_valid = self.validator.is_valid(entry, current_data)
        
        if is_valid:
            entry.touch()
            self._save_cache()
        
        return is_valid
    
    def get_entry(self, cache_key: str) -> Optional[CacheEntry]:
        """
        Get a cache entry by key.
        
        Args:
            cache_key: Cache key to look up
            
        Returns:
            Cache entry if found, None otherwise
        """
        entry = self._cache.get(cache_key)
        if entry:
            entry.touch()
            self._save_cache()
        return entry
    
    def put(
        self, 
        cache_key: str, 
        item_type: str,
        data: Dict[str, Any],
        data_sources: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        status: CacheStatus = CacheStatus.LOADED
    ) -> CacheEntry:
        """
        Put an item in the cache.
        
        Args:
            cache_key: Unique identifier for the cached item
            item_type: Type of item being cached
            data: Data to cache
            data_sources: Optional list of data sources
            metadata: Optional metadata
            status: Initial status of the cached item
            
        Returns:
            Created cache entry
        """
        content_hash = self.config.hash_strategy.compute_hash(data)
        
        entry = CacheEntry(
            cache_key=cache_key,
            item_type=item_type,
            content_hash=content_hash,
            data_sources=data_sources or [],
            status=status,
            metadata=metadata or {}
        )
        
        self._cache[cache_key] = entry
        self._enforce_max_entries()
        self._save_cache()
        
        self.logger.debug(f"Cached item '{cache_key}' of type '{item_type}'")
        return entry
    
    def mark_loading(
        self, 
        cache_key: str, 
        item_type: str,
        data: Dict[str, Any],
        data_sources: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> CacheEntry:
        """
        Mark an item as currently loading.
        
        Args:
            cache_key: Unique identifier for the item
            item_type: Type of item being loaded
            data: Configuration data for the item
            data_sources: Optional list of data sources
            metadata: Optional metadata
            
        Returns:
            Created cache entry
        """
        return self.put(
            cache_key=cache_key,
            item_type=item_type,
            data=data,
            data_sources=data_sources,
            metadata=metadata,
            status=CacheStatus.LOADING
        )
    
    def mark_loaded(self, cache_key: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Mark an item as successfully loaded.
        
        Args:
            cache_key: Cache key of the item
            metadata: Optional additional metadata
            
        Returns:
            True if item was found and updated
        """
        entry = self._cache.get(cache_key)
        if not entry:
            self.logger.warning(f"Cannot mark unknown cache key '{cache_key}' as loaded")
            return False
        
        entry.update_status(CacheStatus.LOADED)
        if metadata:
            for key, value in metadata.items():
                entry.add_metadata(key, value)
        
        self._save_cache()
        self.logger.debug(f"Marked cache key '{cache_key}' as loaded")
        return True
    
    def mark_failed(self, cache_key: str, error_msg: str) -> bool:
        """
        Mark an item as failed to load.
        
        Args:
            cache_key: Cache key of the item
            error_msg: Error message
            
        Returns:
            True if item was found and updated
        """
        entry = self._cache.get(cache_key)
        if not entry:
            self.logger.warning(f"Cannot mark unknown cache key '{cache_key}' as failed")
            return False
        
        entry.update_status(CacheStatus.FAILED, error_msg)
        self._save_cache()
        self.logger.debug(f"Marked cache key '{cache_key}' as failed: {error_msg}")
        return True
    
    def invalidate(self, cache_key: str) -> bool:
        """
        Invalidate a cache entry.
        
        Args:
            cache_key: Cache key to invalidate
            
        Returns:
            True if item was found and removed
        """
        if cache_key in self._cache:
            del self._cache[cache_key]
            self._save_cache()
            self.logger.debug(f"Invalidated cache key '{cache_key}'")
            return True
        return False
    
    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
        self.storage.clear()
        self.logger.info("Cleared all cache entries")
    
    def list_by_status(self, status: CacheStatus) -> List[CacheEntry]:
        """
        Get all cache entries with a specific status.
        
        Args:
            status: Status to filter by
            
        Returns:
            List of cache entries with the specified status
        """
        return [entry for entry in self._cache.values() if entry.status == status]
    
    def list_by_type(self, item_type: str) -> List[CacheEntry]:
        """
        Get all cache entries of a specific type.
        
        Args:
            item_type: Type to filter by
            
        Returns:
            List of cache entries of the specified type
        """
        return [entry for entry in self._cache.values() if entry.item_type == item_type]
    
    def get_keys(self) -> Set[str]:
        """
        Get all cache keys.
        
        Returns:
            Set of all cache keys
        """
        return set(self._cache.keys())
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        total = len(self._cache)
        by_status = {}
        by_type = {}
        
        for entry in self._cache.values():
            # Count by status
            status_name = entry.status.value
            by_status[status_name] = by_status.get(status_name, 0) + 1
            
            # Count by type
            by_type[entry.item_type] = by_type.get(entry.item_type, 0) + 1
        
        return {
            'total_entries': total,
            'by_status': by_status,
            'by_type': by_type,
            'cache_dir': str(self.config.cache_dir),
            'cache_name': self.config.cache_name,
            'hash_strategy': self.config.hash_strategy.get_algorithm_name(),
            'validator_strategy': self.validator.get_validation_strategy_name()
        }
    
    def cleanup_failed(self) -> int:
        """
        Remove all failed cache entries.
        
        Returns:
            Number of entries removed
        """
        failed_keys = [
            key for key, entry in self._cache.items() 
            if entry.status == CacheStatus.FAILED
        ]
        
        for key in failed_keys:
            del self._cache[key]
        
        if failed_keys:
            self._save_cache()
            self.logger.info(f"Cleaned up {len(failed_keys)} failed cache entries")
        
        return len(failed_keys)