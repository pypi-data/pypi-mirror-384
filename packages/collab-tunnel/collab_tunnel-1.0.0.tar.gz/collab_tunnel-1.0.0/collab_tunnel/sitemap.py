"""
Sitemap parser for TCT protocol
"""

from typing import Dict, List, Any, Optional
from datetime import datetime


class SitemapParser:
    """
    Parser for TCT JSON sitemaps.

    Expected sitemap format:
    {
        "version": 1,
        "items": [
            {
                "cUrl": "https://example.com/post/",
                "mUrl": "https://example.com/post/llm/",
                "modified": "2025-10-01T12:34:56Z",
                "contentHash": "sha256-..."
            }
        ]
    }
    """

    def __init__(self, sitemap_data: Dict[str, Any]):
        """
        Initialize sitemap parser.

        Args:
            sitemap_data: Parsed JSON sitemap dictionary

        Raises:
            ValueError: If sitemap format is invalid
        """
        self.data = sitemap_data
        self._validate()

    def _validate(self):
        """Validate sitemap format."""
        if 'items' not in self.data:
            raise ValueError("Sitemap missing 'items' array")

        if not isinstance(self.data['items'], list):
            raise ValueError("Sitemap 'items' must be an array")

        for idx, item in enumerate(self.data['items']):
            required = ['cUrl', 'mUrl', 'contentHash']
            for field in required:
                if field not in item:
                    raise ValueError(
                        f"Sitemap item {idx} missing required field: {field}"
                    )

    @property
    def items(self) -> List[Dict[str, Any]]:
        """Get list of sitemap items."""
        return self.data['items']

    @property
    def version(self) -> int:
        """Get sitemap version."""
        return self.data.get('version', 1)

    @property
    def count(self) -> int:
        """Get total number of items."""
        return len(self.items)

    def filter_by_date(self, since: datetime) -> List[Dict[str, Any]]:
        """
        Filter items modified since a given date.

        Args:
            since: Datetime to filter from

        Returns:
            List of items modified after 'since'
        """
        filtered = []
        for item in self.items:
            modified_str = item.get('modified')
            if not modified_str:
                continue

            modified = datetime.fromisoformat(modified_str.replace('Z', '+00:00'))
            if modified >= since:
                filtered.append(item)

        return filtered

    def find_by_canonical(self, c_url: str) -> Optional[Dict[str, Any]]:
        """
        Find sitemap item by canonical URL.

        Args:
            c_url: Canonical URL to search for

        Returns:
            Matching item or None
        """
        for item in self.items:
            if item['cUrl'] == c_url:
                return item
        return None

    def get_stats(self) -> Dict[str, Any]:
        """
        Get sitemap statistics.

        Returns:
            Dictionary with sitemap stats
        """
        total_size = sum(
            item.get('estimatedSize', 30000) for item in self.items
        )

        return {
            'total_items': self.count,
            'version': self.version,
            'estimated_total_bytes': total_size,
            'has_dates': sum(1 for item in self.items if 'modified' in item),
            'has_hashes': sum(1 for item in self.items if 'contentHash' in item)
        }
