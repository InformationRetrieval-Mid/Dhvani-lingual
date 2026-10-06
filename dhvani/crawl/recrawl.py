"""Adaptive Recrawler: Sitemap monitoring and change-rate tracking."""

from typing import Dict
from dhvani.crawl.config import (
    EWMA_ALPHA,
    MAX_POLL_INTERVAL_SECONDS,
    MIN_POLL_INTERVAL_SECONDS,
)


class AdaptiveRecrawler:
    """Tracks change velocity across news sources to dynamically schedule recrawls."""

    def __init__(self):
        self.last_checked: Dict[str, float] = {}
        self.change_rates: Dict[str, float] = {}

    def get_next_poll_interval(self, source_slug: str) -> float:
        """Calculate next polling interval in seconds."""
        rate = self.change_rates.get(source_slug, 1.0)
        # Scaled interval: faster for active feeds, slower for idle feeds
        interval = MIN_POLL_INTERVAL_SECONDS / max(rate, 0.1)
        return max(MIN_POLL_INTERVAL_SECONDS, min(MAX_POLL_INTERVAL_SECONDS, interval))
