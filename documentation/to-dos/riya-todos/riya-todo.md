# P1: Regional News Crawler & Corpus Pipeline - Checklist

## 1. Project Setup & Configuration
- [x] Create `.gitignore` to keep `data/*.jsonl` and local files off git
- [x] Initialize package layout (`dhvani/`, `dhvani/crawl/`, `dhvani/eval/`, `partwise-tests/riya/`)
- [x] Configure ethical User-Agent with project URL and contact email
- [x] Configure per-host politeness delay (8.0s) and request timeouts
- [x] Define whitelist of 5 primary news sources and 2 backup sources
- [x] Define domain blacklist (BBC Hindi, News18, NDTV)
- [x] Define route exclusion patterns (astrology, photo galleries, videos, live blogs)
- [x] Set Mercator front queue sampling distribution (Q0-Q3)
- [x] Set deduplication thresholds (4-word shingles, Jaccard 0.70, 24h window)

## 2. URL Normalization & Route Filters
- [x] Implement URL scheme and domain lowercasing
- [x] Implement tracking query parameter stripping (`utm_*`, `fbclid`, `ref`, etc.)
- [x] Implement AMP-to-canonical desktop URL mapping
- [x] Implement trailing slash and default port normalization
- [x] Implement blacklist domain filtering
- [x] Implement non-article route filtering

## 3. Robots.txt Compliance (`robots.py`)
- [x] Implement RFC 9309 rules parser
- [x] Implement path pattern matching with `*` and `$` wildcards
- [x] Implement longest-match precedence rule for `Allow` vs `Disallow`
- [x] Implement user-agent group matching (`CollegeProject_NewsBot` with fallback to `*`)
- [x] Implement in-memory per-host caching for parsed rules
- [x] Implement sitemap directive extraction from `robots.txt`
- [x] Write unit tests verifying wildcard support, caching, precedence, and user-agent selection

## 4. Mercator Frontier (`frontier.py`)
- [ ] Implement 4 priority front queues (Q0: Bursts, Q1: Fresh, Q2: Links, Q3: Archive)
- [ ] Implement biased random selector for front queue sampling
- [ ] Implement per-host FIFO back queues for politeness isolation
- [ ] Implement min-heap tracking `(next_allowed_time, host)` to enforce 8.0s delay
- [ ] Implement seen-URL deduplication set
- [ ] Write unit tests verifying 8.0s delay enforcement and queue priorities

## 5. Sitemap & Seed Management (`sitemap.py`)
- [ ] Implement XML sitemap parser for standard sitemaps
- [ ] Implement parser for Google News sitemaps (`<news:news>`, `<news:publication_date>`)
- [ ] Implement sitemap index parser for nested feeds
- [ ] Add archive sitemap seed discovery

## 6. Article & Metadata Extraction (`extractor.py`)
- [ ] Implement Schema.org JSON-LD extraction (`NewsArticle`, `BlogPosting`)
- [ ] Implement HTML fallback extraction (`<h1>`, `<article>`, `<p>`)
- [ ] Implement date parsing to strict ISO-8601 with IST offset (`+05:30`)
- [ ] Implement state and city regex extraction from URL paths
- [ ] Implement section slug extraction and normalization
- [ ] Implement in-body hyperlink extraction for PageRank (`links` field)
- [ ] Enforce zero author names stored in extracted records
- [ ] Validate extracted output against `documentation/formats.md`

## 7. Deduplication & Story Lineage (`dedup.py`)
- [x] Implement MD5 body text hashing for exact duplicates (`content_hash`)
- [x] Implement 4-word sliding shingles generator over Hindi text
- [x] Implement Jaccard similarity calculation
- [x] Implement wire agency keyword detector (`agency_flag`)
- [ ] Implement candidate pair selection within +/- 24-hour temporal window
- [ ] Implement canonical cluster head assignment (`dup_of: null` for earliest, else original `doc_id`)
- [ ] Benchmark MinHash + LSH candidate bucketing (situational fallback)

## 8. Adaptive Recrawling & Event Prioritization
- [ ] Implement sitemap check timestamp tracking per source
- [ ] Implement active period vs idle period check interval scaling (30m to 6h)
- [ ] Add HTTP conditional headers (`If-Modified-Since`, `If-None-Match`/ETag)
- [ ] Implement rolling 60-minute section volume tracking
- [ ] Implement burst surge detection to route breaking URLs into Front Queue Q0

## 9. Crawler Pipeline Execution (`crawler.py`)
- [ ] Integrate sitemap fetcher, frontier, downloader, extractor, and dedup pipeline
- [ ] Add polite backoff on HTTP 403, 429, or network errors
- [ ] Implement streaming JSONL writer to `data/news.jsonl`
- [ ] Crawl and generate 300-article sample for team handoff (`data/news_sample_300.jsonl` - H3)
- [ ] Complete full crawl to reach 5,000-12,000 articles (Corpus Freeze - H18)

## 10. Shared Tooling & Downstream Support (`eval/pool.py`, handoffs)
- [x] Implement TREC run pooling function (`pool_runs`)
- [ ] Complete CLI for run file pooling and judgment template generation (`formats.md` #5)
- [ ] Document data ingestion and pre-work in `documentation/handoffs/riya.md`

## 11. Test Suite (`partwise-tests/riya/`)
- [x] `test_robots.py`: Benchmark custom parser vs `urllib.robotparser` bugs
- [ ] `test_frontier.py`: Validate 8.0s per-host delay and front queue weighting
- [ ] `test_normalizer.py`: Validate query stripping and AMP conversion
- [ ] `test_extractor.py`: Validate JSON-LD extraction, IST dates, and absence of authors
- [ ] `test_dedup.py`: Measure precision and recall on 100 labeled article pairs
- [ ] `test_format_compliance.py`: Validate schema compliance with `formats.md`

## 12. Evaluation & Submission Deliverables
- [ ] Generate deduplication threshold precision/recall table
- [ ] Generate crawler corpus statistics (articles per source, section distribution)
- [ ] Write report section (crawling architecture, robots.txt findings, deduplication)
- [ ] Record video segment (crawler log, robots tests, duplicate story grouping)
