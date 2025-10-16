"""
Hash strategy implementations for the cache system.

This module provides concrete implementations of different hashing strategies
that can be used to generate content hashes for cache validation.
"""

import hashlib
import json
from typing import Any, Dict

from .base import HashStrategy


class ConfigHasher(HashStrategy):
    """
    Hash strategy for configuration objects.
    
    This hasher creates deterministic hashes of configuration dictionaries
    by normalizing and sorting the JSON representation.
    """
    
    def compute_hash(self, data: Dict[str, Any]) -> str:
        """
        Compute a SHA256 hash of configuration data.
        
        Args:
            data: Configuration data to hash
            
        Returns:
            SHA256 hash string
        """
        # Create a normalized string representation of the config
        # Sort keys and use compact separators for deterministic output
        config_str = json.dumps(data, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(config_str.encode('utf-8')).hexdigest()
    
    def get_algorithm_name(self) -> str:
        """Get the algorithm name."""
        return "SHA256-JSON"


class ContentHasher(HashStrategy):
    """
    Hash strategy for arbitrary content.
    
    This hasher can handle various types of content including strings,
    bytes, and complex data structures.
    """
    
    def compute_hash(self, data: Dict[str, Any]) -> str:
        """
        Compute a SHA256 hash of content data.
        
        Args:
            data: Content data to hash
            
        Returns:
            SHA256 hash string
        """
        # Handle different types of content
        if isinstance(data, dict):
            # For dictionaries, use JSON serialization
            content_str = json.dumps(data, sort_keys=True, separators=(',', ':'))
        elif isinstance(data, (list, tuple)):
            # For sequences, convert to JSON
            content_str = json.dumps(list(data), sort_keys=True, separators=(',', ':'))
        elif isinstance(data, str):
            # For strings, use directly
            content_str = data
        elif isinstance(data, bytes):
            # For bytes, decode if possible, otherwise use hex representation
            try:
                content_str = data.decode('utf-8')
            except UnicodeDecodeError:
                content_str = data.hex()
        else:
            # For other types, convert to string
            content_str = str(data)
        
        return hashlib.sha256(content_str.encode('utf-8')).hexdigest()
    
    def get_algorithm_name(self) -> str:
        """Get the algorithm name."""
        return "SHA256-Content"


class MD5Hasher(HashStrategy):
    """
    MD5 hash strategy (less secure but faster).
    
    This hasher uses MD5 for scenarios where cryptographic security
    is not required but speed is important.
    """
    
    def compute_hash(self, data: Dict[str, Any]) -> str:
        """
        Compute an MD5 hash of the data.
        
        Args:
            data: Data to hash
            
        Returns:
            MD5 hash string
        """
        config_str = json.dumps(data, sort_keys=True, separators=(',', ':'))
        return hashlib.md5(config_str.encode('utf-8')).hexdigest()
    
    def get_algorithm_name(self) -> str:
        """Get the algorithm name."""
        return "MD5-JSON"


class CombinedHasher(HashStrategy):
    """
    Combined hash strategy that uses multiple hashers.
    
    This hasher combines multiple hash strategies to create
    more robust change detection.
    """
    
    def __init__(self, *hashers: HashStrategy):
        """
        Initialize with multiple hashers.
        
        Args:
            *hashers: Hash strategies to combine
        """
        if not hashers:
            raise ValueError("At least one hasher must be provided")
        self.hashers = hashers
    
    def compute_hash(self, data: Dict[str, Any]) -> str:
        """
        Compute a combined hash using all configured hashers.
        
        Args:
            data: Data to hash
            
        Returns:
            Combined hash string
        """
        # Compute hash with each hasher and combine them
        hashes = []
        for hasher in self.hashers:
            hash_value = hasher.compute_hash(data)
            hashes.append(f"{hasher.get_algorithm_name()}:{hash_value}")
        
        # Create a final hash of all the individual hashes
        combined_str = "|".join(hashes)
        return hashlib.sha256(combined_str.encode('utf-8')).hexdigest()
    
    def get_algorithm_name(self) -> str:
        """Get the algorithm name."""
        hasher_names = [hasher.get_algorithm_name() for hasher in self.hashers]
        return f"Combined({','.join(hasher_names)})"