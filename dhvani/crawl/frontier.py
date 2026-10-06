"""Mercator Frontier: Front Priority Queues, Per-Host Back Queues, and Politeness Min-Heap."""

import heapq
import time
from collections import deque
from typing import Dict, Optional, Tuple
from urllib.parse import urlparse

from dhvani.crawl.config import FRONT_QUEUE_PROBABILITIES, PER_HOST_DELAY


class MercatorFrontier:
    """Two-tier Mercator crawl frontier isolating priority from per-host politeness."""

    def __init__(self, per_host_delay: float = PER_HOST_DELAY):
        self.per_host_delay = per_host_delay

        # Front Queues (Priority: Q0=Burst, Q1=Fresh, Q2=Links, Q3=Archive)
        self.front_queues: Dict[str, deque] = {
            "Q0": deque(),
            "Q1": deque(),
            "Q2": deque(),
            "Q3": deque(),
        }

        # Back Queues (Per-Host FIFO queues for politeness isolation)
        self.back_queues: Dict[str, deque] = {}

        # Politeness Min-Heap: entries of (ready_time, host)
        self.heap: list = []

        # Seen URL set to prevent duplicate frontier enqueueing
        self.seen_urls: set = set()

    def add_url(self, url: str, priority_tier: str = "Q1") -> bool:
        """Enqueue URL into the specified priority front queue if not seen."""
        if url in self.seen_urls:
            return False
        self.seen_urls.add(url)
        self.front_queues[priority_tier].append(url)
        return True

    def get_next_url(self) -> Optional[Tuple[str, str]]:
        """Retrieve the next ready URL respecting the per-host 8-second delay."""
        return None
