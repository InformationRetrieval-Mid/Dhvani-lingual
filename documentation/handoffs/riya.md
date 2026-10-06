# P1 Corpus Generation & Handoff Instructions

## 1. Generate H3 Milestone Sample (300 Articles)
To generate the 300-article sample deliverable for downstream search engine indexing (Dhrithi / P2), run:

```bash
python -m dhvani.crawl.crawler --sample
```
* **Output Path:** `data/news_sample_300.jsonl`
* **Target Count:** Exactly 300 validated articles
* **Estimated Runtime:** ~8 to 10 minutes (cycling 5 primary news sources with 8.0s per-host politeness delay)

## 2. Generate Full Master Corpus (5,000 Articles)
To run the full crawl for the complete master corpus, run:

```bash
python -m dhvani.crawl.crawler --max-articles 5000
```
* **Output Path:** `data/news.jsonl`
* **Target Count:** 5,000 validated articles
* **Estimated Runtime:** ~2.2 hours
* **Note:** The crawler automatically snapshots the first 300 articles to `data/news_sample_300.jsonl` upon reaching article #300 during the run.

## 3. Sample Corpus Verification & Statistics Report
A comprehensive audit and statistical breakdown of the 300-article sample deliverable (including source balance, section distribution, district-level city mapping, and vocabulary metrics) is documented at:
* [`data/results/sample_300_stats.md`](../../data/results/sample_300_stats.md)

