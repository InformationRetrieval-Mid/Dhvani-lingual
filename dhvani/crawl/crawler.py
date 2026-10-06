"""Dhvani Regional News Crawler (P1).

Orchestrates sitemap feed ingestion, RFC 9309 robots checking, Mercator frontier
priority scheduling, polite per-host rate limiting, resilient HTTP downloading,
3-tier article extraction, and streaming JSONL storage.
"""

import argparse
import asyncio
from collections import defaultdict
import json
import logging
from pathlib import Path
import re
import sys
import time
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse

import httpx

from dhvani.crawl.config import (
    ARTICLES_FILE,
    BACKOFF_FACTOR,
    DEFAULT_HEADERS,
    DEFAULT_TIMEOUT,
    MAX_RETRIES,
    PER_HOST_DELAY,
    PRIMARY_SOURCES,
    SAMPLE_ARTICLES_FILE,
    USER_AGENT,
)
from dhvani.crawl.extractor import ArticleExtractor, validate_article_schema
from dhvani.crawl.filters import should_skip_url
from dhvani.crawl.frontier import MercatorFrontier
from dhvani.crawl.normalizer import normalize_url
from dhvani.crawl.robots import RobotsParser
from dhvani.crawl.sitemap import SitemapParser

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("dhvani.crawler")

# Mapping of known domains to standardized source keys
SOURCE_MAP: Dict[str, str] = {
    "jagran.com": "jagran",
    "www.jagran.com": "jagran",
    "navbharattimes.indiatimes.com": "nbt",
    "livehindustan.com": "livehindustan",
    "www.livehindustan.com": "livehindustan",
    "amarujala.com": "amarujala",
    "www.amarujala.com": "amarujala",
    "aajtak.in": "aajtak",
    "www.aajtak.in": "aajtak",
    "jansatta.com": "jansatta",
    "www.jansatta.com": "jansatta",
    "bhaskar.com": "bhaskar",
    "www.bhaskar.com": "bhaskar",
}

# Signatures indicating genuine bot challenge or CAPTCHA interception screens
CAPTCHA_SIGNATURES = [
    "cf-challenge-running",
    "challenge-platform",
    "cf-browser-verification",
    "captcha-delivery.com",
    "px-captcha",
    "distil_r_captcha",
    "Attention Required! | Cloudflare",
    "<title>Just a moment...</title>",
]


def get_source_key(url: str) -> str:
    """Resolve source identifier from URL domain."""
    if not url:
        return "unknown"
    netloc = urlparse(url).netloc.lower()
    if netloc in SOURCE_MAP:
        return SOURCE_MAP[netloc]
    for domain, key in SOURCE_MAP.items():
        if domain in netloc:
            return key
    # Fallback to base domain name
    parts = netloc.split(".")
    return parts[-2] if len(parts) >= 2 else netloc


def is_captcha_challenge(html: str) -> bool:
    """Check if HTML content indicates an anti-bot CAPTCHA / challenge interception."""
    if not html:
        return False
    # Legitimate news articles containing structured metadata or article containers
    # are never anti-bot challenge screens.
    if "schema.org" in html and ("NewsArticle" in html or "BlogPosting" in html):
        return False
    if "<article" in html:
        return False
    html_sample = html[:5000]
    return any(sig.lower() in html_sample.lower() for sig in CAPTCHA_SIGNATURES)


class NewsCrawler:
    """Asynchronous regional news crawler orchestrator."""

    def __init__(
        self,
        frontier: Optional[MercatorFrontier] = None,
        robots_parser: Optional[RobotsParser] = None,
        sitemap_parser: Optional[SitemapParser] = None,
        extractor: Optional[ArticleExtractor] = None,
        max_articles: int = 5000,
        is_sample_mode: bool = False,
        output_path: Optional[Path] = None,
        sample_output_path: Optional[Path] = None,
        active_sources: Optional[List[str]] = None,
        time_func=time.time,
    ):
        self.is_sample_mode = is_sample_mode
        self.max_articles = 300 if is_sample_mode else max_articles

        self.output_path = Path(output_path or (SAMPLE_ARTICLES_FILE if is_sample_mode else ARTICLES_FILE))
        self.sample_output_path = Path(sample_output_path or SAMPLE_ARTICLES_FILE)

        self.frontier = frontier or MercatorFrontier(per_host_delay=PER_HOST_DELAY)
        self.robots = robots_parser or RobotsParser(user_agent=USER_AGENT)
        self.sitemap_parser = sitemap_parser or SitemapParser()
        self.extractor = extractor or ArticleExtractor()
        self.time_func = time_func

        self.active_sources = active_sources or list(PRIMARY_SOURCES.keys())

        # Progress tracking
        self.saved_articles_count: int = 0
        self.articles_by_source: Dict[str, int] = defaultdict(int)
        self.seen_doc_ids: Set[str] = set()
        self.sample_records: List[Dict[str, Any]] = []
        self._sample_snapshot_saved: bool = False

        # Host health and politeness controls
        self.disabled_hosts: Set[str] = set()
        self.host_delays: Dict[str, float] = {}

        self.start_time: float = 0.0

    def get_host_delay(self, host: str) -> float:
        """Get the current scheduling delay for host (default 8.0s or backed-off)."""
        return self.host_delays.get(host, self.frontier.per_host_delay)

    async def bootstrap_seeds(self, client: httpx.AsyncClient) -> int:
        """Discover and enqueue initial URLs from sitemaps of configured sources."""
        total_enqueued = 0
        logger.info("Bootstrapping seeds across sources: %s", ", ".join(self.active_sources))

        urls_by_source: Dict[str, List[str]] = defaultdict(list)

        for source_key in self.active_sources:
            source_cfg = PRIMARY_SOURCES.get(source_key)
            if not source_cfg:
                continue

            domain = source_cfg.get("domain", "")
            robots_url = source_cfg.get("robots_url", "")
            sitemap_urls = list(source_cfg.get("sitemaps", []))

            # Fetch robots.txt to discover additional sitemaps
            if robots_url:
                try:
                    r_resp = await client.get(robots_url, timeout=DEFAULT_TIMEOUT)
                    if r_resp.status_code == 200:
                        self.robots.set_cached_rules(domain, r_resp.text)
                        discovered_sitemaps = self.robots.extract_sitemaps(r_resp.text)
                        for s_url in discovered_sitemaps:
                            if s_url not in sitemap_urls:
                                sitemap_urls.append(s_url)
                except Exception as e:
                    logger.warning("Could not fetch robots.txt for %s: %s", domain, e)

            # Fetch and parse discovered sitemaps
            for s_url in sitemap_urls:
                try:
                    s_resp = await client.get(s_url, timeout=DEFAULT_TIMEOUT)
                    if s_resp.status_code == 200:
                        content = s_resp.text
                        if self.sitemap_parser.is_sitemap_index(content):
                            child_sitemaps = self.sitemap_parser.parse_sitemap_index(content)
                            # Sample up to 3 child sitemaps per index to seed without overwhelming
                            for child_url, _ in child_sitemaps[:3]:
                                try:
                                    c_resp = await client.get(child_url, timeout=DEFAULT_TIMEOUT)
                                    if c_resp.status_code == 200:
                                        entries = self.sitemap_parser.parse_sitemap(c_resp.text)
                                        for entry in entries:
                                            urls_by_source[source_key].append(entry.url)
                                except Exception as ce:
                                    logger.debug("Failed child sitemap %s: %s", child_url, ce)
                        else:
                            entries = self.sitemap_parser.parse_sitemap(content)
                            for entry in entries:
                                urls_by_source[source_key].append(entry.url)
                except Exception as se:
                    logger.warning("Failed sitemap %s: %s", s_url, se)

        # Round-robin interleave URLs across sources into Frontier Q1
        max_source_urls = max((len(u) for u in urls_by_source.values()), default=0)
        per_source_seed_cap = 500 if self.is_sample_mode else 3000
        for idx in range(min(max_source_urls, per_source_seed_cap)):
            for source_key in self.active_sources:
                if idx < len(urls_by_source[source_key]):
                    candidate = urls_by_source[source_key][idx]
                    if self.frontier.add_url(candidate, priority_tier="Q1"):
                        total_enqueued += 1

        logger.info(
            "Seed bootstrap complete. Enqueued %d initial URLs interleaved across %d sources.",
            total_enqueued,
            len(urls_by_source),
        )
        return total_enqueued

    async def fetch_article_html(
        self, client: httpx.AsyncClient, url: str, host: str
    ) -> Tuple[Optional[str], Optional[int], Optional[str]]:
        """Fetch article page over HTTP with retry backoff on transient errors.

        Returns: (html_text, status_code, error_message)
        """
        retries = 0
        backoff = 1.0

        while retries <= MAX_RETRIES:
            try:
                response = await client.get(url, timeout=DEFAULT_TIMEOUT, follow_redirects=True)
                status = response.status_code

                if status == 200:
                    html_text = response.text
                    if is_captcha_challenge(html_text):
                        return None, 403, "CAPTCHA challenge detected"
                    return html_text, 200, None

                if status == 429:
                    return None, 429, "Too Many Requests"

                if status == 403:
                    return None, 403, "Forbidden"

                if 500 <= status < 600:
                    retries += 1
                    if retries <= MAX_RETRIES:
                        await asyncio.sleep(backoff)
                        backoff *= BACKOFF_FACTOR
                        continue
                    return None, status, f"Server Error {status}"

                # Non-retriable 4xx
                return None, status, f"Client Error {status}"

            except (httpx.TimeoutException, httpx.NetworkError) as ne:
                retries += 1
                if retries <= MAX_RETRIES:
                    await asyncio.sleep(backoff)
                    backoff *= BACKOFF_FACTOR
                    continue
                return None, 0, f"Network exception: {ne}"
            except Exception as e:
                return None, 0, f"Unexpected fetch error: {e}"

        return None, 0, "Retries exhausted"

    def harvest_links(self, links: List[str]) -> int:
        """Filter, normalize, and enqueue discovered in-body links into Frontier Q2."""
        added = 0
        for link in links:
            if not link:
                continue
            clean_link = normalize_url(link)
            if not clean_link or clean_link in self.frontier.seen_urls:
                continue
            if should_skip_url(clean_link):
                continue
            if self.frontier.add_url(clean_link, priority_tier="Q2"):
                added += 1
        return added

    def write_record(self, record: Dict[str, Any], file_handle) -> None:
        """Stream a validated record to disk and manage H3 sample snapshots."""
        line = json.dumps(record, ensure_ascii=False)
        file_handle.write(line + "\n")
        file_handle.flush()

        self.seen_doc_ids.add(record["doc_id"])

        # Track first 300 records for the sample deliverable
        if not self.is_sample_mode and len(self.sample_records) < 300:
            self.sample_records.append(record)
            if len(self.sample_records) == 300 and not self._sample_snapshot_saved:
                self._save_sample_snapshot()

    def _save_sample_snapshot(self) -> None:
        """Save retained first 300 articles to sample output file."""
        self.sample_output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.sample_output_path, "w", encoding="utf-8") as f:
            for rec in self.sample_records:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        self._sample_snapshot_saved = True
        logger.info("Successfully exported H3 sample snapshot: %s (300 articles)", self.sample_output_path)

    def print_progress(self) -> None:
        """Display live progress dashboard on console."""
        elapsed = max(self.time_func() - self.start_time, 0.001)
        rate = (self.saved_articles_count / elapsed) * 60.0
        pct = (self.saved_articles_count / self.max_articles) * 100.0 if self.max_articles else 0.0

        source_stats = " | ".join(f"{s}: {count}" for s, count in sorted(self.articles_by_source.items()))
        logger.info(
            "Progress: %d/%d (%.1f%%) | %.1f art/min | Frontier: %d queued | Sources: [%s]",
            self.saved_articles_count,
            self.max_articles,
            pct,
            rate,
            self.frontier.size(),
            source_stats,
        )

    async def crawl(self, client: Optional[httpx.AsyncClient] = None) -> int:
        """Main crawl loop executing until target count is reached or frontier drains."""
        self.start_time = self.time_func()
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        close_client = False
        if client is None:
            client = httpx.AsyncClient(
                headers=DEFAULT_HEADERS,
                timeout=DEFAULT_TIMEOUT,
                limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
            )
            close_client = True

        try:
            # Seed frontier
            await self.bootstrap_seeds(client)

            # In sample mode, overwrite previous sample runs for a clean deliverable;
            # in normal mode, append to support resuming long crawls.
            file_mode = "w" if self.is_sample_mode else "a"
            with open(self.output_path, file_mode, encoding="utf-8") as out_f:
                while self.saved_articles_count < self.max_articles and not self.frontier.is_empty():
                    next_item = await self.frontier.get_next_url()
                    if next_item is None:
                        if self.frontier.is_empty():
                            logger.info("Frontier completely drained.")
                            break
                        await asyncio.sleep(0.5)
                        continue

                    url, host = next_item

                    # Skip disabled hosts (403 / CAPTCHA)
                    if host in self.disabled_hosts:
                        self.frontier.complete_request(host, delay=self.get_host_delay(host))
                        continue

                    # Check robots.txt compliance
                    if not self.robots.can_fetch(url):
                        logger.debug("Robots disallowed URL: %s", url)
                        self.frontier.complete_request(host, delay=self.get_host_delay(host))
                        continue

                    # Fetch and extract
                    eff_delay = self.get_host_delay(host)
                    try:
                        html, status, err = await self.fetch_article_html(client, url, host)

                        if status == 429:
                            # Exponential backoff on rate-limit
                            curr_delay = self.get_host_delay(host)
                            eff_delay = min(curr_delay * BACKOFF_FACTOR, 64.0)
                            self.host_delays[host] = eff_delay
                            logger.warning("Host %s returned 429. Increasing delay to %.1fs", host, eff_delay)

                        elif status == 403 or (err and "CAPTCHA" in err):
                            logger.warning("Host %s intercepted (%s: %s). Disabling for crawl session.", host, status, err)
                            self.disabled_hosts.add(host)

                        elif status == 200 and html:
                            # Reset delay if host is healthy
                            if host in self.host_delays:
                                self.host_delays[host] = self.frontier.per_host_delay
                                eff_delay = self.frontier.per_host_delay

                            source_key = get_source_key(url)
                            article = self.extractor.extract(html, url=url, source_slug=source_key)

                            if article and article["doc_id"] not in self.seen_doc_ids:
                                if validate_article_schema(article):
                                    self.write_record(article, out_f)
                                    self.saved_articles_count += 1
                                    self.articles_by_source[source_key] += 1

                                    # Harvest links
                                    if article.get("links"):
                                        self.harvest_links(article["links"])

                                    if self.saved_articles_count % 10 == 0 or self.saved_articles_count == self.max_articles:
                                        self.print_progress()
                                else:
                                    logger.debug("Schema invalid for %s", url)

                    finally:
                        # Politeness guarantee: always reschedule host
                        self.frontier.complete_request(host, delay=eff_delay)

            # Snapshot save if crawl finished early without reaching 300
            if not self.is_sample_mode and not self._sample_snapshot_saved and self.sample_records:
                self._save_sample_snapshot()

            logger.info("Crawl session finished. Total valid articles saved: %d", self.saved_articles_count)
            return self.saved_articles_count

        finally:
            if close_client:
                await client.aclose()


def main():
    """CLI Entry point for Dhvani Regional News Crawler."""
    parser = argparse.ArgumentParser(description="Dhvani Regional News Crawler (P1)")
    parser.add_argument("--sample", action="store_true", help="Crawl 300 articles for H3 handoff")
    parser.add_argument("--max-articles", type=int, default=5000, help="Target article limit (default: 5000)")
    parser.add_argument("--sources", type=str, default="", help="Comma-separated subset of sources to crawl")
    parser.add_argument("--output", type=str, default="", help="Custom output JSONL path")
    args = parser.parse_args()

    active_sources = [s.strip() for s in args.sources.split(",") if s.strip()] or None
    output_path = Path(args.output) if args.output else None

    crawler = NewsCrawler(
        max_articles=args.max_articles,
        is_sample_mode=args.sample,
        output_path=output_path,
        active_sources=active_sources,
    )

    try:
        asyncio.run(crawler.crawl())
    except KeyboardInterrupt:
        logger.info("Crawl manually stopped by user. Progress saved.")


if __name__ == "__main__":
    main()
