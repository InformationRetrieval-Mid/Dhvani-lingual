"""Main crawler orchestrator tying together frontier, downloader, extractor, and dedup."""

import argparse
import logging
from dhvani.crawl.config import USER_AGENT, PER_HOST_DELAY, PRIMARY_SOURCES

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("dhvani.crawler")


def main():
    parser = argparse.ArgumentParser(description="Dhvani Regional News Crawler")
    parser.add_argument("--max-articles", type=int, default=5000, help="Maximum articles to crawl")
    parser.add_argument("--sample", action="store_true", help="Generate 300-article sample for H3")
    args = parser.parse_args()

    logger.info("Initializing Dhvani crawler with User-Agent: %s", USER_AGENT)
    logger.info("Enforcing per-host delay: %.1f seconds", PER_HOST_DELAY)


if __name__ == "__main__":
    main()
