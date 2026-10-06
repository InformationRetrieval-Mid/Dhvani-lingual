"""Deduplication Engine: Exact Hash, 4-word Shingles, Jaccard, MinHash + LSH."""

import hashlib
from typing import List, Optional, Set, Tuple
from dhvani.crawl.config import SHINGLE_SIZE, JACCARD_THRESHOLD, WIRE_AGENCY_KEYWORDS


def compute_content_hash(text: str) -> str:
    """Compute MD5 hash of normalized, whitespace-stripped text."""
    normalized = " ".join(text.strip().split())
    return hashlib.md5(normalized.encode("utf-8")).hexdigest()


def generate_shingles(text: str, n: int = SHINGLE_SIZE) -> Set[str]:
    """Generate n-word sliding shingles from Hindi text."""
    words = text.strip().split()
    if len(words) < n:
        return {" ".join(words)}
    return {" ".join(words[i:i + n]) for i in range(len(words) - n + 1)}


def jaccard_similarity(set_a: Set[str], set_b: Set[str]) -> float:
    """Calculate Jaccard similarity coefficient between two sets."""
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union if union > 0 else 0.0


def is_agency_story(text: str) -> bool:
    """Detect if text contains syndicated wire agency keywords (PTI, ANI, Bhasha, etc.)."""
    for kw in WIRE_AGENCY_KEYWORDS:
        if kw in text:
            return True
    return False
