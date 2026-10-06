"""Sitemap fetcher and XML parser for news-sitemap and standard sitemaps."""

from typing import List, Tuple


class SitemapParser:
    """Parses standard XML sitemaps and Google News sitemaps."""

    def parse_sitemap(self, xml_content: str) -> List[Tuple[str, Optional[str]]]:
        """Extract (url, lastmod) pairs from sitemap XML string."""
        return []

    def parse_sitemap_index(self, xml_content: str) -> List[str]:
        """Extract child sitemap URLs from a sitemap index file."""
        return []
