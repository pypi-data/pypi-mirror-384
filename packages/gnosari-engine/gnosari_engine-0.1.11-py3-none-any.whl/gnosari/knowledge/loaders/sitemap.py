"""
Sitemap loader for OpenSearch knowledge bases.
"""

import asyncio
import logging
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional, Set
from urllib.parse import urljoin, urlparse
import aiohttp

from .base import BaseLoader
from .website import WebsiteLoader


class SitemapParser:
    """Handles XML sitemap parsing and URL extraction."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def parse_sitemap_content(self, content: str) -> Dict[str, List[str]]:
        """
        Parse XML sitemap content and extract URLs and nested sitemaps.
        
        Args:
            content: XML sitemap content
            
        Returns:
            Dictionary with 'urls' and 'sitemaps' lists
        """
        try:
            root = ET.fromstring(content)
            
            # Handle sitemap index (references to other sitemaps)
            if self._is_sitemap_index(root):
                return self._parse_sitemap_index(root)
            
            # Handle regular sitemap (list of URLs)
            return self._parse_url_set(root)
            
        except ET.ParseError as e:
            self.logger.error(f"Failed to parse XML sitemap: {str(e)}")
            return {"urls": [], "sitemaps": []}
    
    def _is_sitemap_index(self, root: ET.Element) -> bool:
        """Check if XML root is a sitemap index."""
        return root.tag.endswith('}sitemapindex') or root.tag == 'sitemapindex'
    
    def _parse_sitemap_index(self, root: ET.Element) -> Dict[str, List[str]]:
        """Parse sitemap index and extract nested sitemap URLs."""
        sitemaps = []
        
        for sitemap_elem in root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}sitemap'):
            loc_elem = sitemap_elem.find('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
            if loc_elem is not None and loc_elem.text:
                sitemaps.append(loc_elem.text.strip())
        
        # Also check for elements without namespace
        for sitemap_elem in root.findall('.//sitemap'):
            loc_elem = sitemap_elem.find('.//loc')
            if loc_elem is not None and loc_elem.text:
                sitemaps.append(loc_elem.text.strip())
        
        return {"urls": [], "sitemaps": sitemaps}
    
    def _parse_url_set(self, root: ET.Element) -> Dict[str, List[str]]:
        """Parse URL set and extract page URLs."""
        urls = []
        
        for url_elem in root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}url'):
            loc_elem = url_elem.find('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
            if loc_elem is not None and loc_elem.text:
                urls.append(loc_elem.text.strip())
        
        # Also check for elements without namespace
        for url_elem in root.findall('.//url'):
            loc_elem = url_elem.find('.//loc')
            if loc_elem is not None and loc_elem.text:
                urls.append(loc_elem.text.strip())
        
        return {"urls": urls, "sitemaps": []}


class SitemapDiscovery:
    """Handles recursive discovery of sitemaps."""
    
    def __init__(self, max_depth: int = 5):
        self.max_depth = max_depth
        self.logger = logging.getLogger(__name__)
        self.parser = SitemapParser()
    
    async def discover_all_urls(self, sitemap_url: str) -> List[str]:
        """
        Recursively discover all URLs from sitemap and nested sitemaps.
        
        Args:
            sitemap_url: Root sitemap URL
            
        Returns:
            List of all discovered URLs
        """
        discovered_urls = []
        visited_sitemaps: Set[str] = set()
        
        await self._discover_recursive(sitemap_url, discovered_urls, visited_sitemaps, 0)
        
        return discovered_urls
    
    async def _discover_recursive(
        self, 
        sitemap_url: str, 
        discovered_urls: List[str], 
        visited_sitemaps: Set[str], 
        depth: int
    ) -> None:
        """Recursively discover URLs from sitemaps with parallel processing."""
        if depth > self.max_depth:
            self.logger.warning(f"Max depth {self.max_depth} reached, stopping recursion")
            return
        
        if sitemap_url in visited_sitemaps:
            self.logger.debug(f"Already visited sitemap: {sitemap_url}")
            return
        
        visited_sitemaps.add(sitemap_url)
        self.logger.info(f"Processing sitemap at depth {depth}: {sitemap_url}")
        
        try:
            content = await self._fetch_sitemap_content(sitemap_url)
            if not content:
                return
            
            parsed = self.parser.parse_sitemap_content(content)
            
            # Add discovered URLs
            discovered_urls.extend(parsed["urls"])
            self.logger.info(f"Found {len(parsed['urls'])} URLs in sitemap: {sitemap_url}")
            
            # Process nested sitemaps in parallel
            if parsed["sitemaps"]:
                nested_tasks = []
                for nested_sitemap in parsed["sitemaps"]:
                    nested_url = urljoin(sitemap_url, nested_sitemap)
                    if nested_url not in visited_sitemaps:  # Check before creating task
                        task = self._discover_recursive(
                            nested_url, discovered_urls, visited_sitemaps, depth + 1
                        )
                        nested_tasks.append(task)
                
                if nested_tasks:
                    await asyncio.gather(*nested_tasks, return_exceptions=True)
        
        except Exception as e:
            self.logger.error(f"Error processing sitemap {sitemap_url}: {str(e)}")
    
    async def _fetch_sitemap_content(self, url: str) -> Optional[str]:
        """Fetch sitemap content from URL."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.text()
                    else:
                        self.logger.error(f"Failed to fetch sitemap {url}: HTTP {response.status}")
                        return None
        except Exception as e:
            self.logger.error(f"Error fetching sitemap {url}: {str(e)}")
            return None


class SitemapLoader(BaseLoader):
    """Sitemap loader that discovers URLs from sitemaps and loads their content."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize sitemap loader.
        
        Args:
            config: Optional loader configuration
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self.website_loader = WebsiteLoader(config)
        self.discovery = SitemapDiscovery(
            max_depth=self.config.get('max_sitemap_depth', 5)
        )
        
        # Concurrency configuration
        self.max_concurrent_urls = self.config.get('max_concurrent_urls', 10)
        self.max_concurrent_sitemaps = self.config.get('max_concurrent_sitemaps', 5)
    
    async def load_data(self, source: str, metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Load data from sitemap URL by discovering all URLs and fetching their content.
        
        Args:
            source: Sitemap URL
            metadata: Optional metadata to add to documents
            
        Returns:
            List of documents with 'text' field and metadata
        """
        self.logger.info(f"SitemapLoader: Loading data from sitemap {source}")
        
        try:
            # Discover all URLs from sitemap
            urls = await self.discovery.discover_all_urls(source)
            
            if not urls:
                self.logger.warning(f"No URLs found in sitemap: {source}")
                return []
            
            self.logger.info(f"Discovered {len(urls)} URLs from sitemap: {source}")
            
            # Filter URLs if configured
            urls = self._filter_urls(urls)
            
            # Limit URLs if configured
            max_urls = self.config.get('max_urls', None)
            if max_urls and len(urls) > max_urls:
                self.logger.info(f"Limiting to first {max_urls} URLs")
                urls = urls[:max_urls]
            
            # Load content from all discovered URLs in parallel
            all_documents = []
            
            # Create parallel tasks for content loading
            content_tasks = []
            for i, url in enumerate(urls):
                # Add sitemap-specific metadata
                url_metadata = {
                    "sitemap_source": source,
                    "url_index": i,
                    "total_urls": len(urls),
                    "loader": "sitemap"
                }
                if metadata:
                    url_metadata.update(metadata)
                
                # Create task for loading this URL's content
                task = self._load_url_content(url, url_metadata, i + 1, len(urls))
                content_tasks.append(task)
            
            # Execute all content loading tasks in parallel with concurrency limit
            self.logger.info(f"Loading content from {len(urls)} URLs in parallel (max concurrent: {self.max_concurrent_urls})")
            
            # Use semaphore to limit concurrent requests
            semaphore = asyncio.Semaphore(self.max_concurrent_urls)
            limited_tasks = [self._load_url_with_semaphore(semaphore, task) for task in content_tasks]
            
            results = await asyncio.gather(*limited_tasks, return_exceptions=True)
            
            # Process results and collect documents
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    self.logger.error(f"Failed to load content from URL {i+1}: {str(result)}")
                elif isinstance(result, list):
                    all_documents.extend(result)
            
            self.logger.info(f"SitemapLoader: Loaded {len(all_documents)} total documents from {len(urls)} URLs")
            return all_documents
            
        except Exception as e:
            self.logger.error(f"Error loading sitemap content from {source}: {str(e)}")
            return []
    
    async def _load_url_content(
        self, 
        url: str, 
        url_metadata: Dict[str, Any], 
        url_num: int, 
        total_urls: int
    ) -> List[Dict[str, Any]]:
        """Load content from a single URL."""
        try:
            self.logger.info(f"Loading content from URL {url_num}/{total_urls}: {url}")
            documents = await self.website_loader.load_data(url, url_metadata)
            return documents
        except Exception as e:
            self.logger.error(f"Error loading content from URL {url}: {str(e)}")
            return []
    
    async def _load_url_with_semaphore(self, semaphore: asyncio.Semaphore, task) -> List[Dict[str, Any]]:
        """Execute URL loading task with semaphore to limit concurrency."""
        async with semaphore:
            return await task
    
    def _filter_urls(self, urls: List[str]) -> List[str]:
        """Filter URLs based on configuration."""
        if not urls:
            return urls
        
        # Filter by allowed patterns
        allowed_patterns = self.config.get('allowed_url_patterns', [])
        if allowed_patterns:
            filtered_urls = []
            for url in urls:
                if any(pattern in url for pattern in allowed_patterns):
                    filtered_urls.append(url)
            urls = filtered_urls
        
        # Filter out blocked patterns
        blocked_patterns = self.config.get('blocked_url_patterns', [])
        if blocked_patterns:
            urls = [url for url in urls if not any(pattern in url for pattern in blocked_patterns)]
        
        # Remove duplicates while preserving order
        seen = set()
        unique_urls = []
        for url in urls:
            if url not in seen:
                seen.add(url)
                unique_urls.append(url)
        
        return unique_urls