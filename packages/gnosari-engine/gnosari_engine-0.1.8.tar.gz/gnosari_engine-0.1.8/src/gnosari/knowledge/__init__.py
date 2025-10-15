"""
Knowledge management package for Gnosari AI Teams.

This package provides knowledge base functionality including:
- Base interfaces for knowledge systems
- Embedchain integration adapter
- Knowledge managers for RAG operations
- Generic cache system integration
"""

from .base import BaseKnowledgeBase, KnowledgeQuery, KnowledgeResult
from .manager import KnowledgeManager
from .embedchain_adapter import EmbedchainKnowledgeBase

__all__ = [
    'BaseKnowledgeBase',
    'KnowledgeQuery', 
    'KnowledgeResult',
    'KnowledgeManager',
    'EmbedchainKnowledgeBase'
]