"""
Collaboration Tunnel Protocol Crawler
Implements efficient web crawling using sitemap-first discovery and conditional requests.
"""

import requests
import hashlib
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from .sitemap import SitemapParser
from .validator import ContentValidator


class CollabTunnelCrawler:
    """
    Main crawler class for TCT protocol.

    Example usage:
        crawler = CollabTunnelCrawler()
        sitemap = crawler.fetch_sitemap("https://example.com/llm-sitemap.json")

        for item in sitemap.items:
            if crawler.should_fetch(item):
                content = crawler.fetch_content(item['mUrl'], item['contentHash'])
                # Process content...
    """

    def __init__(self,
                 user_agent: str = "CollabTunnelCrawler/1.0",
                 cache_dir: str = ".cache",
                 verify_ssl: bool = True):
        """
        Initialize the crawler.

        Args:
            user_agent: User agent string to identify the crawler
            cache_dir: Directory to store cached content hashes
            verify_ssl: Whether to verify SSL certificates
        """
        self.user_agent = user_agent
        self.cache_dir = cache_dir
        self.verify_ssl = verify_ssl
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.stats = {
            'requests': 0,
            'bytes_downloaded': 0,
            'bytes_saved': 0,
            'cache_hits': 0,
            'zero_fetches': 0
        }

    def fetch_sitemap(self, sitemap_url: str) -> SitemapParser:
        """
        Fetch and parse a TCT sitemap.

        Args:
            sitemap_url: URL to the JSON sitemap (e.g., /llm-sitemap.json)

        Returns:
            SitemapParser object containing parsed sitemap data

        Raises:
            requests.RequestException: If sitemap fetch fails
            ValueError: If sitemap format is invalid
        """
        response = requests.get(
            sitemap_url,
            headers={'User-Agent': self.user_agent},
            verify=self.verify_ssl,
            timeout=30
        )
        response.raise_for_status()

        self.stats['requests'] += 1
        self.stats['bytes_downloaded'] += len(response.content)

        sitemap_data = response.json()
        return SitemapParser(sitemap_data)

    def should_fetch(self, item: Dict[str, Any]) -> bool:
        """
        Determine if content should be fetched based on cached hash.

        This implements the "zero-fetch" optimization: if the content hash
        in the sitemap matches our cached hash, we skip fetching entirely.

        Args:
            item: Sitemap item with 'mUrl' and 'contentHash' keys

        Returns:
            True if content should be fetched, False if it can be skipped
        """
        m_url = item.get('mUrl')
        new_hash = item.get('contentHash')

        if not m_url or not new_hash:
            return True  # Missing data, fetch to be safe

        cached = self.cache.get(m_url)
        if not cached:
            return True  # Not in cache, need to fetch

        if cached.get('contentHash') == new_hash:
            # Hash matches! Zero-fetch optimization
            self.stats['zero_fetches'] += 1
            self.stats['bytes_saved'] += cached.get('estimated_size', 30000)
            return False

        return True  # Hash changed, need to fetch

    def fetch_content(self,
                     m_url: str,
                     expected_hash: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Fetch content from M-URL with conditional request.

        Args:
            m_url: Machine-readable endpoint URL
            expected_hash: Expected content hash (from sitemap) for validation

        Returns:
            Parsed JSON content if fetched, None if 304 Not Modified

        Raises:
            requests.RequestException: If request fails
            ValueError: If content hash doesn't match expected
        """
        headers = {'User-Agent': self.user_agent}

        # Add If-None-Match header if we have cached ETag
        cached = self.cache.get(m_url)
        if cached and 'etag' in cached:
            headers['If-None-Match'] = cached['etag']

        response = requests.get(
            m_url,
            headers=headers,
            verify=self.verify_ssl,
            timeout=30
        )

        self.stats['requests'] += 1

        # Handle 304 Not Modified
        if response.status_code == 304:
            self.stats['cache_hits'] += 1
            self.stats['bytes_saved'] += cached.get('estimated_size', 30000)
            return None  # Content unchanged

        response.raise_for_status()

        # Track bandwidth
        content_length = len(response.content)
        self.stats['bytes_downloaded'] += content_length

        # Get ETag for caching
        etag = response.headers.get('ETag')

        # Parse JSON content
        content = response.json()

        # Validate content hash if provided
        if expected_hash:
            actual_hash = content.get('hash')
            if actual_hash and not self._hashes_match(expected_hash, actual_hash):
                raise ValueError(
                    f"Content hash mismatch: expected {expected_hash}, got {actual_hash}"
                )

        # Update cache
        self.cache[m_url] = {
            'etag': etag,
            'contentHash': expected_hash or content.get('hash'),
            'fetched_at': datetime.utcnow().isoformat(),
            'estimated_size': content_length
        }

        return content

    def verify_handshake(self, c_url: str, m_url: str) -> bool:
        """
        Verify bidirectional C-URL ↔ M-URL handshake.

        Checks:
        1. C-URL HTML contains <link rel="alternate" href="M-URL">
        2. M-URL headers contain Link: <C-URL>; rel="canonical"

        Args:
            c_url: Canonical URL
            m_url: Machine-readable URL

        Returns:
            True if handshake is valid, False otherwise
        """
        # Check C-URL → M-URL link
        c_response = requests.get(c_url, headers={'User-Agent': self.user_agent})
        c_html = c_response.text

        if f'href="{m_url}"' not in c_html or 'rel="alternate"' not in c_html:
            return False

        # Check M-URL → C-URL link
        m_response = requests.head(m_url, headers={'User-Agent': self.user_agent})
        link_header = m_response.headers.get('Link', '')

        if f'<{c_url}>' not in link_header or 'rel="canonical"' not in link_header:
            return False

        return True

    def get_stats(self) -> Dict[str, Any]:
        """
        Get crawler statistics.

        Returns:
            Dictionary with crawl stats including bandwidth savings
        """
        total_bytes = self.stats['bytes_downloaded'] + self.stats['bytes_saved']
        savings_pct = (self.stats['bytes_saved'] / total_bytes * 100) if total_bytes > 0 else 0

        return {
            'requests': self.stats['requests'],
            'bytes_downloaded': self.stats['bytes_downloaded'],
            'bytes_saved': self.stats['bytes_saved'],
            'savings_percentage': round(savings_pct, 1),
            'cache_hits_304': self.stats['cache_hits'],
            'zero_fetches': self.stats['zero_fetches'],
            'total_skips': self.stats['cache_hits'] + self.stats['zero_fetches']
        }

    def _hashes_match(self, hash1: str, hash2: str) -> bool:
        """Compare two hashes, handling different formats (with/without sha256- prefix)."""
        h1 = hash1.replace('sha256-', '').replace('"', '')
        h2 = hash2.replace('sha256-', '').replace('"', '')
        return h1 == h2


# Convenience function
def crawl_site(sitemap_url: str,
               limit: Optional[int] = None,
               user_agent: str = "CollabTunnelCrawler/1.0") -> List[Dict[str, Any]]:
    """
    Crawl an entire site using TCT protocol.

    Example:
        results = crawl_site("https://example.com/llm-sitemap.json", limit=100)
        for result in results:
            print(result['title'], result['content'][:100])

    Args:
        sitemap_url: URL to sitemap
        limit: Maximum number of items to crawl (None = all)
        user_agent: User agent string

    Returns:
        List of crawled content dictionaries
    """
    crawler = CollabTunnelCrawler(user_agent=user_agent)
    sitemap = crawler.fetch_sitemap(sitemap_url)

    results = []
    items = sitemap.items[:limit] if limit else sitemap.items

    for item in items:
        if crawler.should_fetch(item):
            content = crawler.fetch_content(item['mUrl'], item.get('contentHash'))
            if content:
                results.append(content)

    print(f"Crawl complete: {crawler.get_stats()}")
    return results
