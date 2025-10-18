"""
Content validator for TCT protocol
"""

import hashlib
import re
from typing import Dict, Any, List, Optional


class ContentValidator:
    """
    Validates TCT protocol compliance and content integrity.
    """

    @staticmethod
    def validate_etag(etag: str, content: str) -> bool:
        """
        Validate that ETag matches content hash.

        Args:
            etag: ETag header value (e.g., "sha256-abc123...")
            content: Content text to hash

        Returns:
            True if ETag matches content hash
        """
        # Extract hash from ETag (remove quotes and sha256- prefix)
        etag_hash = etag.replace('"', '').replace('sha256-', '')

        # Normalize content (lowercase, collapse whitespace)
        normalized = ContentValidator.normalize_text(content)

        # Compute SHA256
        computed_hash = hashlib.sha256(normalized.encode('utf-8')).hexdigest()

        return etag_hash == computed_hash

    @staticmethod
    def normalize_text(text: str) -> str:
        """
        Normalize text following TCT spec:
        - Lowercase
        - Collapse whitespace to single space
        - Normalize punctuation

        Args:
            text: Input text

        Returns:
            Normalized text
        """
        # Lowercase
        text = text.lower()

        # Collapse whitespace
        text = re.sub(r'\s+', ' ', text)

        # Normalize quotes
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace(''', "'").replace(''', "'")

        # Trim
        text = text.strip()

        return text

    @staticmethod
    def check_headers(headers: Dict[str, str]) -> Dict[str, Any]:
        """
        Check TCT protocol compliance of HTTP headers.

        Args:
            headers: Dictionary of HTTP headers

        Returns:
            Dictionary with compliance check results
        """
        results = {
            'compliant': True,
            'checks': {},
            'errors': []
        }

        # Check Content-Type
        content_type = headers.get('content-type', '').lower()
        results['checks']['json_content_type'] = 'application/json' in content_type

        if not results['checks']['json_content_type']:
            results['errors'].append("Content-Type should be application/json")
            results['compliant'] = False

        # Check ETag
        etag = headers.get('etag')
        results['checks']['etag_present'] = bool(etag)
        results['checks']['etag_format'] = False

        if etag:
            results['checks']['etag_format'] = etag.startswith('"sha256-')
            if not results['checks']['etag_format']:
                results['errors'].append("ETag should start with 'sha256-'")
                results['compliant'] = False
        else:
            results['errors'].append("ETag header missing")
            results['compliant'] = False

        # Check Link canonical
        link = headers.get('link', '')
        results['checks']['canonical_link'] = 'rel="canonical"' in link

        if not results['checks']['canonical_link']:
            results['errors'].append("Link header missing rel='canonical'")
            results['compliant'] = False

        # Check Cache-Control
        cache_control = headers.get('cache-control', '').lower()
        results['checks']['must_revalidate'] = 'must-revalidate' in cache_control

        if not results['checks']['must_revalidate']:
            results['errors'].append("Cache-Control should include must-revalidate")

        # Check Vary
        vary = headers.get('vary', '').lower()
        results['checks']['vary_accept'] = 'accept' in vary

        if not results['checks']['vary_accept']:
            results['errors'].append("Vary header should include Accept")

        return results

    @staticmethod
    def validate_sitemap_item(item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a single sitemap item structure.

        Args:
            item: Sitemap item dictionary

        Returns:
            Validation results
        """
        results = {
            'valid': True,
            'errors': []
        }

        # Check required fields
        required_fields = ['cUrl', 'mUrl', 'contentHash']
        for field in required_fields:
            if field not in item:
                results['errors'].append(f"Missing required field: {field}")
                results['valid'] = False

        # Check URL format
        if 'cUrl' in item and not item['cUrl'].startswith('http'):
            results['errors'].append("cUrl must be absolute URL")
            results['valid'] = False

        if 'mUrl' in item and not item['mUrl'].startswith('http'):
            results['errors'].append("mUrl must be absolute URL")
            results['valid'] = False

        # Check hash format
        if 'contentHash' in item:
            hash_val = item['contentHash']
            if not (hash_val.startswith('sha256-') or re.match(r'^[a-f0-9]{64}$', hash_val)):
                results['errors'].append("contentHash must be sha256 hash")
                results['valid'] = False

        # Check modified date format (if present)
        if 'modified' in item:
            modified = item['modified']
            if not re.match(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', modified):
                results['errors'].append("modified must be ISO 8601 format")
                results['valid'] = False

        return results
