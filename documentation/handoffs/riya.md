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

## 3. Corpus Verification & Statistics Reports
Comprehensive audits and statistical breakdowns of the crawled corpus and deduplication clustering are documented at:
* [`data/result-documentation/sample_corpus_stats.md`](../../data/result-documentation/sample_corpus_stats.md): Source balance, section breakdown, district-level city mapping, and vocabulary metrics.
* [`data/result-documentation/dedup_stats.md`](../../data/result-documentation/dedup_stats.md): Deduplication clustering yield, pairwise similarity spectrum, and threshold calibration.

