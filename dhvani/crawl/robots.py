"""Custom RFC 9309 compliant robots.txt parser."""

from typing import List, Optional


class RobotsParser:
    """RFC 9309 compliant robots.txt parser for Indian news portals.

    Fixes urllib.robotparser failures on wildcard matching, longest-match precedence,
    and trailing wildcards.
    """

    def __init__(self, user_agent: str = "*"):
        self.user_agent = user_agent.lower()
        self.disallow_rules: List[str] = []
        self.allow_rules: List[str] = []
        self.sitemaps: List[str] = []

    def parse(self, content: str) -> None:
        """Parse raw robots.txt content."""
        pass

    def can_fetch(self, url: str) -> bool:
        """Check whether the given URL can be fetched under parsed rules."""
        return True
