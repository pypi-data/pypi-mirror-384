"""
Collaboration Tunnel Protocol - Python Client Library
Version: 1.0.0
Author: Antun Jurkovikj
License: MIT

A Python library for efficiently crawling websites that implement the
Collaboration Tunnel Protocol (TCT), achieving 60-90% bandwidth savings
through sitemap-first discovery and conditional requests.
"""

__version__ = '1.0.0'

from .crawler import CollabTunnelCrawler
from .sitemap import SitemapParser
from .validator import ContentValidator

__all__ = ['CollabTunnelCrawler', 'SitemapParser', 'ContentValidator']
