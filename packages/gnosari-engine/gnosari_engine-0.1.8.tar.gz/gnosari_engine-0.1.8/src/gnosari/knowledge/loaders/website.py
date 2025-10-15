"""
Website loader for OpenSearch knowledge bases.
"""

import logging
import os
import time
from typing import Any, Dict, List, Optional
import aiohttp

from .base import BaseLoader


class WebsiteLoader(BaseLoader):
    """Website loader that fetches content through a markdown conversion API."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize website loader.
        
        Args:
            config: Optional loader configuration
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self.api_host = os.getenv("WEBSITE_LOADER_API_HOST", "https://r.ai.neomanex.com")
    
    async def load_data(self, source: str, metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Load data from website URL using markdown conversion API with text chunking.

        Args:
            source: Website URL
            metadata: Optional metadata to add to documents
            
        Returns:
            List of documents with 'text' field and metadata
        """
        self.logger.info(f"WebsiteLoader: Loading data from {source}")
        
        try:
            api_url = f"{self.api_host}/{source}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url) as response:
                    if response.status == 200:
                        content = await response.text()
                        
                        # Chunk the content for better embedding generation
                        chunks = self._chunk_text(content)
                        self.logger.info(f"WebsiteLoader: Split content into {len(chunks)} chunks")
                        
                        documents = []
                        for i, chunk in enumerate(chunks):
                            # Clean the chunk text to avoid API parsing issues
                            cleaned_chunk = self._clean_text(chunk)
                            
                            # Skip empty chunks
                            if not cleaned_chunk.strip():
                                self.logger.debug(f"Skipping empty chunk {i}")
                                continue
                                
                            doc_metadata = {
                                "source": source, 
                                "loader": "website",
                                "chunk_index": i,
                                "total_chunks": len(chunks)
                            }
                            if metadata:
                                doc_metadata.update(metadata)
                                
                            documents.append({
                                "text": cleaned_chunk,
                                "metadata": doc_metadata,
                                "timestamp": time.strftime('%Y-%m-%dT%H:%M:%S')
                            })
                        
                        return documents
                    else:
                        self.logger.error(f"Failed to fetch content from {api_url}: HTTP {response.status}")
                        return []
                        
        except Exception as e:
            self.logger.error(f"Error loading website content from {source}: {str(e)}")
            return []
    
    def _chunk_text(self, text: str) -> List[str]:
        """
        Chunk text into smaller pieces suitable for embedding generation.
        
        Args:
            text: Input text to chunk
            
        Returns:
            List of text chunks
        """
        # Get chunk size from config (default to ~8000 characters to stay under token limits)
        chunk_size = self.config.get('chunk_size', 8000)
        chunk_overlap = self.config.get('chunk_overlap', 200)
        
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            if end >= len(text):
                # Last chunk
                chunks.append(text[start:])
                break
            
            # Try to break at a sentence boundary
            chunk_text = text[start:end]
            
            # Look for sentence endings in the last 500 characters
            sentence_endings = ['. ', '! ', '? ', '\n\n']
            best_break = -1
            
            for ending in sentence_endings:
                pos = chunk_text.rfind(ending)
                if pos > len(chunk_text) - 500:  # Only consider breaks near the end
                    best_break = max(best_break, pos + len(ending))
            
            if best_break > 0:
                chunk_text = text[start:start + best_break]
                chunks.append(chunk_text)
                start = start + best_break - chunk_overlap
            else:
                # No good break found, just split at chunk_size
                chunk_text = text[start:end]
                chunks.append(chunk_text)
                start = end - chunk_overlap
            
            # Ensure we don't go backwards
            if start < 0:
                start = 0
        
        return chunks
    
    def _clean_text(self, text: str) -> str:
        """
        Clean text to remove problematic characters that might cause API issues.
        
        Args:
            text: Input text to clean
            
        Returns:
            Cleaned text
        """
        import re
        
        # Remove or replace problematic characters
        # Replace excessive whitespace with single spaces
        text = re.sub(r'\s+', ' ', text)
        
        # Only allow safe characters: letters, numbers, punctuation, and markdown-safe symbols
        # This comprehensive approach removes all potentially problematic Unicode characters
        allowed_chars = set()
        
        # Basic ASCII letters, numbers, and punctuation
        for i in range(32, 127):  # Printable ASCII
            allowed_chars.add(chr(i))
        
        # Add essential whitespace characters
        allowed_chars.update(['\n', '\r', '\t'])
        
        # Filter text to only include allowed characters
        text = ''.join(char for char in text if char in allowed_chars)
        
        # Fix fragment starts - if text starts with lowercase or incomplete sentence
        text = self._fix_fragment_start(text)
        
        # Strip whitespace
        text = text.strip()
        
        return text
    
    def _fix_fragment_start(self, text: str) -> str:
        """
        Fix fragment starts by finding the first complete sentence.
        
        Args:
            text: Input text that may start with a fragment
            
        Returns:
            Text starting with a complete sentence
        """
        import re
        
        # If text starts with a lowercase letter or incomplete word, try to find the first complete sentence
        if text and (text[0].islower() or text.startswith(('to ', 'and ', 'or ', 'but ', 'the ', 'a ', 'an '))):
            # Look for the first sentence ending followed by a capital letter
            sentence_pattern = r'[.!?]\s+[A-Z#*]'
            match = re.search(sentence_pattern, text)
            if match:
                # Start from the capital letter after the sentence ending
                start_pos = match.start() + len(match.group()) - 1
                text = text[start_pos:]
                self.logger.debug(f"Fixed fragment start, new text begins with: '{text[:50]}...'")
        
        return text