"""
Cache entry system for representing individual cached items.

This module provides the core data structures for tracking cached items
with their status, metadata, and validation information.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional


class CacheStatus(Enum):
    """
    Enumeration of possible cache entry statuses.
    
    This provides type-safe status tracking with clear semantics.
    """
    LOADING = "loading"      # Item is currently being loaded/processed
    LOADED = "loaded"        # Item has been successfully loaded and cached
    FAILED = "failed"        # Item failed to load/process
    EXPIRED = "expired"      # Item has expired and needs refresh
    INVALID = "invalid"      # Item is invalid due to configuration changes


@dataclass
class CacheEntry:
    """
    Represents a single cached item with metadata and status tracking.
    
    This class follows the Single Responsibility Principle by only
    handling the data and state of a cached item.
    """
    
    # Core identification
    cache_key: str
    item_type: str  # e.g., "knowledge_base", "model_config", etc.
    
    # Content and validation
    content_hash: str
    data_sources: list[str] = field(default_factory=list)
    
    # Timestamps
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_accessed: str = field(default_factory=lambda: datetime.now().isoformat()) 
    last_modified: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # Status tracking
    status: CacheStatus = CacheStatus.LOADING
    
    # Flexible metadata storage
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Optional expiration
    expires_at: Optional[str] = None
    
    def touch(self) -> None:
        """Update the last accessed timestamp."""
        self.last_accessed = datetime.now().isoformat()
    
    def mark_modified(self) -> None:
        """Update the last modified timestamp."""
        self.last_modified = datetime.now().isoformat()
        self.touch()
    
    def is_expired(self) -> bool:
        """
        Check if this cache entry has expired.
        
        Returns:
            True if the entry has expired
        """
        if not self.expires_at:
            return False
        
        try:
            expiry_time = datetime.fromisoformat(self.expires_at)
            return datetime.now() > expiry_time
        except (ValueError, TypeError):
            # If we can't parse the expiry time, consider it expired
            return True
    
    def set_expiry(self, expiry_time: datetime) -> None:
        """
        Set the expiry time for this cache entry.
        
        Args:
            expiry_time: When this entry should expire
        """
        self.expires_at = expiry_time.isoformat()
    
    def add_metadata(self, key: str, value: Any) -> None:
        """
        Add metadata to this cache entry.
        
        Args:
            key: Metadata key
            value: Metadata value
        """
        self.metadata[key] = value
        self.mark_modified()
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """
        Get metadata from this cache entry.
        
        Args:
            key: Metadata key
            default: Default value if key not found
            
        Returns:
            Metadata value or default
        """
        return self.metadata.get(key, default)
    
    def update_status(self, status: CacheStatus, error_msg: Optional[str] = None) -> None:
        """
        Update the status of this cache entry.
        
        Args:
            status: New status
            error_msg: Optional error message if status is FAILED
        """
        self.status = status
        self.mark_modified()
        
        if status == CacheStatus.FAILED and error_msg:
            self.add_metadata('error', error_msg)
        elif status != CacheStatus.FAILED and 'error' in self.metadata:
            # Clear error if status is no longer failed
            del self.metadata['error']
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert this cache entry to a dictionary for serialization.
        
        Returns:
            Dictionary representation of this entry
        """
        data = asdict(self)
        # Convert enum to string for JSON serialization
        data['status'] = self.status.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CacheEntry':
        """
        Create a cache entry from a dictionary.
        
        Args:
            data: Dictionary containing cache entry data
            
        Returns:
            New CacheEntry instance
        """
        # Convert string status back to enum
        if 'status' in data and isinstance(data['status'], str):
            try:
                data['status'] = CacheStatus(data['status'])
            except ValueError:
                # If we can't parse the status, default to INVALID
                data['status'] = CacheStatus.INVALID
        
        return cls(**data)
    
    def __str__(self) -> str:
        """String representation of this cache entry."""
        return f"CacheEntry(key={self.cache_key}, type={self.item_type}, status={self.status.value})"
    
    def __repr__(self) -> str:
        """Detailed string representation of this cache entry."""
        return (f"CacheEntry(cache_key={self.cache_key!r}, item_type={self.item_type!r}, "
                f"content_hash={self.content_hash!r}, status={self.status!r}, "
                f"created_at={self.created_at!r})")