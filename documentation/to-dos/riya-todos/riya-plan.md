# Crawler & Corpus Pipeline 
**Component:** P1 - Regional News Crawler, Corpus & Shared Tooling  
**Deliverable:** `data/news.jsonl` (following `documentation/formats.md`)  
**Shared Tool:** `dhvani/eval/pool.py` (TREC run pooling)

---

## 1. Scope & Crawling Rules

### Target Sites
* **5 Primary Sites:**
  1. *Dainik Jagran* (`jagran.com`)
  2. *Navbharat Times* (`navbharattimes.indiatimes.com`)
  3. *Live Hindustan* (`livehindustan.com`)
  4. *Amar Ujala* (`amarujala.com`)
  5. *Aaj Tak* (`aajtak.in`)
* **Backups:** *Jansatta* (`jansatta.com`), *Dainik Bhaskar* (`bhaskar.com`).
* **Corpus Target:** ~5,000 articles from live sitemaps (up to ~12,000 using archive sitemaps).

### Ethical Crawling Guidelines
* **User-Agent:** Use an honest, descriptive name: `CollegeProject_NewsBot(+https://github.com/InformationRetrieval-Mid/Dhvani-lingual; contact: ra810@snu.edu.in)`.
* **Politeness:** Minimum **8.0 seconds delay** between consecutive requests to the same site.
* **Privacy:** **Store no author names** anywhere in the dataset.
* **Storage Policy:** Article text stays local on your machine (`data/news.jsonl` is gitignored). Only crawler code and URLs are committed to GitHub.
* **Error Handling:** Stop/back off on HTTP 403, 429, or CAPTCHA encounters.

---

## 2. Directory Structure
```text
dhvani/
├── crawl/
│   ├── __init__.py
│   ├── config.py             # Sites whitelist, timeouts, 8s rate limit, user-agent
│   ├── robots.py             # Custom RFC 9309 robots.txt parser
│   ├── frontier.py           # Mercator frontier (front priority queues + politeness min-heap)
│   ├── sitemap.py            # Sitemap fetcher and parser (news-sitemap.xml + archives)
│   ├── normalizer.py         # URL normalization & AMP-to-canonical mapping
│   ├── filters.py            # Route filters (skips rashifal/astrology, photos, videos)
│   ├── extractor.py          # JSON-LD article extractor with HTML <p> fallback
│   ├── dedup.py              # Shingles, Jaccard, MinHash + LSH, story clustering
│   ├── recrawl.py            # Adaptive freshness & change-rate tracking
│   └── crawler.py            # Main crawler loop & CLI runner
│
└── eval/
    ├── __init__.py
    └── pool.py               # Shared pooling script for TREC run files
```

---

## 3. Core Components & Implementation Design

### 1. Custom Robots.txt Checker (`robots.py`)
#### The Problem
Python's built-in `urllib.robotparser` gives incorrect answers on Indian news portals (Jagran, Jansatta, Live Hindustan, Amar Ujala) because it fails on wildcard (`*`) matching, end-of-URL (`$`) matching, query parameters, and longest-match precedence rules.

#### Implementation Design
* Implement a custom RFC 9309-compliant parser.
* Support wildcards (`*`) and longest-match rule (`Allow` vs `Disallow`).
* Parse `Sitemap:` directives directly from `robots.txt`.
* Unit tests in `partwise-tests/riya/test_robots.py` will demonstrate exact test cases where `urllib.robotparser` fails and our parser succeeds (a great talking point for the report).

---

### 2. Mercator Frontier Architecture (`frontier.py`)
#### How It Works
Separates priority from politeness using a two-tier queue structure:
```text
               [ Incoming URLs: Sitemaps, Bursts, In-Page Links ]
                                    │
                                    ▼
       ┌────────────────────────────────────────────────────────┐
       │                 FRONT QUEUES (Priority)                │
       │   Q0: Bursts (60%)           Q1: Fresh Sitemaps (25%)  │
       │   Q2: In-Page Links (10%)    Q3: Archive Sitemaps (5%) │
       └────────────────────────────┬───────────────────────────┘
                                    │ Biased Random Selector
                                    ▼
       ┌────────────────────────────────────────────────────────┐
       │                BACK QUEUES (Politeness)                │
       │   [Jagran]   [Navbharat]   [Hindustan]   [AmarUjala]   │
       └────────────────────────────┬───────────────────────────┘
                                    │
                                    ▼
               ┌────────────────────────────────────────┐
               │         POLITENESS MIN-HEAP            │
               │  Entries: (next_allowed_time, host)    │
               │  Enforces 8-second delay per host      │
               └────────────────────────────────────────┘
```

#### Queue Loop
1. Min-Heap inspects top entry `(ready_time, host)`.
2. If `ready_time > now()`, worker sleeps for `ready_time - now()`.
3. Pop next URL from `host`'s FIFO back queue.
4. Fetch URL, extract content, write to `data/news.jsonl`.
5. Reschedule `host` on the heap with `ready_time = now() + 8.0s`.

---

### 3. Adaptive Recrawling (`recrawl.py`)
#### Why It's Feasible
News sites publish sitemaps (`sitemap.xml` / `news-sitemap.xml`) updated throughout the day. Instead of polling every site on a rigid timer, track the empirical publication rate $\lambda_s$ of each source.

#### Implementation Design
* **Track Source Velocity:** Count new URLs added ($\Delta N$) over elapsed time ($\Delta t$) each time a sitemap is checked:
  $$\lambda_s^{(t)} = \alpha \cdot \frac{\Delta N}{\Delta t} + (1 - \alpha) \cdot \lambda_s^{(t-1)} \quad (\text{EWMA with } \alpha = 0.3)$$
* **Dynamic Polling Schedule:** Compute next sitemap check interval $\tau_s$:
  $$\tau_s = \max\left(\tau_{\min},\; \min\left(\tau_{\max},\; \frac{K}{\lambda_s + \epsilon}\right)\right)$$
  - $\tau_{\min} = 30\text{ minutes}$ (breaking news sources during peak hours).
  - $\tau_{\max} = 6\text{ hours}$ (slower weekend/night sources or archive sitemaps).
* **Conditional Fetching:** Send `If-Modified-Since` or `If-None-Match` (ETag) headers. A `304 Not Modified` terminates immediately, saving bandwidth and processing.

---

### 4. Event / Burst-Aware Prioritization
#### Why It's Feasible
Breaking events (e.g. weather alerts, elections, accidents) produce sharp spikes in article volume under specific sections. This can be detected without heavy ML models.

#### Implementation Design
* **Detecting the Burst:**
  - Track article publication count in a rolling 60-minute window per section (`weather`, `state`, `national`).
  - Calculate burst ratio against the 6-hour moving average:
    $$\text{BurstScore}(\text{category}) = \frac{\text{Count}_{1\text{h}}}{\text{MovingAvg}_{6\text{h}} + 1}$$
* **Front Queue Routing:**
  - If $\text{BurstScore} > 2.0$, new URLs from that category route into **Front Queue $Q_0$ (Highest Priority)**.
  - Biased selector samples: $P(Q_0)=0.60$, $P(Q_1)=0.25$, $P(Q_2)=0.10$, $P(Q_3)=0.05$.
* **Politeness Preserved:** Prioritization only decides which URL is placed next in that host's back queue. Network requests remain strictly gated by the min-heap at 8 seconds per host.

---

### 5. URL Normalization & Route Filtering (`normalizer.py`, `filters.py`)
#### Normalization
* Lowercase scheme and host.
* Strip tracking query params: `utm_*`, `ref`, `fbclid`, `amp_js_v`.
* Map AMP pages to canonical desktop URLs (drop `/amp/`, `?amp=1`).
* Strip default ports and trailing slashes.

#### Filters
* Skip non-article pages:
  - Astrology/Horoscope: `/rashifal/`, `/astrology/`, `/horoscope/` (avoids keyword pollution).
  - Media: `/photo-gallery/`, `/photos/`, `/videos/`.
  - Live blogs without full text: `/live-updates/`.

---

### 6. Article & Metadata Extraction (`extractor.py`)
#### Extraction Strategy
* **Primary:** Parse Schema.org JSON-LD (`schema.org/NewsArticle` or `BlogPosting`).
* **Fallback:** Standard HTML tags (`<article>`, `<h1>`, `<p>`).
* **Fields Extracted:**
  - `headline`: Title string in Devanagari.
  - `body`: Clean body text without ads, captions, or navigation.
  - `date`: Publication timestamp converted to **ISO-8601 in IST (`+05:30`)**.
  - `section`: Normalized category slug.
  - `state` / `city`: Extracted from URL path patterns (e.g., `/lucknow/` $\to$ `city: "lucknow"`).
  - `keywords`: Extracted from metadata.
  - `links`: Collect in-body `<a href="...">` links to other crawled articles (for PageRank).
  - **No author names** stored.

---

### 7. Near-Duplicate & Story Clustering (`dedup.py`)
#### Why It's Feasible
Newspapers frequently republish identical or slightly reworded wire stories from PTI, ANI, and Univarta/Bhasha.

#### Implementation Design
* **Exact Duplicates:** MD5 hash of normalized body text $\to$ `content_hash`.
* **Syntactic Near-Duplicates (MinHash + LSH):**
  - Extract 4-word shingles over Hindi text.
  - Compute 64-permutation MinHash signatures, hashed into $b=16$ bands of $r=4$ rows.
  - Candidate comparison restricted to articles within a **$\pm 24$-hour window**.
* **Story Clustering for `dup_of`:**
  - Compute Jaccard on candidate pairs: $J(A, B) = \frac{|A \cap B|}{|A \cup B|}$.
  - If Jaccard $\ge 0.70$:
    - The earliest published article is the root (`dup_of: null`).
    - Later articles point to it (`dup_of: "<earliest_doc_id>"`).
* **Agency Flag:** Detect wire keywords (`"पीटीआई"`, `"भाषा"`, `"वार्ता"`, `"ANI"`, `"PTI"`) and set `agency_flag: true`.

---

### 8. Crawl Budget & Timing Sanity Check
$$\text{Throughput} = \frac{5 \text{ sites}}{8.0 \text{ s/request}} = 0.625 \text{ req/s} \approx 2,250 \text{ articles/hour}$$
* **To crawl 5,000 articles:** $\approx 2.2 \text{ hours}$ of active crawling across all 5 sites.
* **To crawl 12,000 articles:** $\approx 5.3 \text{ hours}$.
* 5 sites run round-robin, so no site blocks others while waiting for its 8-second delay.

### 9. Shared Tooling: TREC Run Pooling (`dhvani/eval/pool.py`)
* Read standard TREC run files: `qid Q0 doc_id rank score run_name`.
* Extract top-$k$ ($k=10$ or $20$) documents per information need across all runs.
* Deduplicate documents and generate human judgment sheets: `need_id 0 doc_id rel`.

---

### 10. Optional Enhancement: Neural / Semantic Utility Prioritization (`dhvani/crawl/utility.py`)
#### Why It's Feasible & Grounded in IR
Standard focused crawlers target a specific query, which is unsuited for a general search engine where queries are unknown in advance. Instead, we use a **retrieval-agnostic Corpus Utility model** $\mathcal{U}(u) \in [0, 1]$.
It estimates how much valuable, novel, and substantive information an unvisited URL will add to the overall corpus, using strictly crawl-time features without touching search queries or test relevance labels.

#### Crawl-Time Features Available (Retrieval-Agnostic)
1. **Anchor / Headline Text:** Discovered from referring page `<a href="...">anchor</a>` or `<news:title>` in sitemaps.
2. **Entity Density:** Salient entities (Hindi city names, state names, numbers/dates) present in the anchor/title text.
3. **URL Depth & Section Weight:** High-information sections (`national`, `state`, `weather`) prioritized over shallow filler.
4. **Corpus Novelty (Semantic Distance):** Using a lightweight embedding model (e.g. `paraphrase-multilingual-MiniLM-L12-v2` or fastText):
   - Compute embedding $\vec{e}_u$ of the candidate title/anchor text.
   - Compare against the running centroid $\vec{c}_{\text{sec}}$ of articles already crawled in that category.
   - Novelty score: $\text{Nov}(u) = 1 - \cos(\vec{e}_u, \vec{c}_{\text{sec}})$.
5. **Structural In-Degree:** Number of internal pages linking to this candidate URL.

#### Utility Score Formulation
$$\mathcal{U}(u) = w_1 \cdot \text{InformationDensity}(u) + w_2 \cdot \text{Novelty}(u) + w_3 \cdot \text{Freshness}(u) + w_4 \cdot \text{SectionWeight}(u)$$

#### Integration into Mercator Front Queues
The utility score determines Front Queue routing:
* $Q_0$ (Highest Priority): $\mathcal{U}(u) \ge 0.75$
* $Q_1$ (High Priority): $0.50 \le \mathcal{U}(u) < 0.75$
* $Q_2$ (Standard Priority): $0.25 \le \mathcal{U}(u) < 0.50$
* $Q_3$ (Low / Archive): $\mathcal{U}(u) < 0.25$

#### Politeness Preserved
The utility score only controls which front queue receives the URL. Per-host back queues and the min-heap strictly enforce the 8.0s per-host delay.

#### Downstream Pre-work
Crawl-time utility scores $\mathcal{U}(u)$ can be exported alongside articles as a pre-computed static document quality feature $g(d)$ for downstream ranking.

---

## 4. Contract Compliance: `documentation/formats.md`
All crawled articles must be written to `data/news.jsonl` (one JSON line per article):
```json
{
  "doc_id": "jagran_23456789",
  "url": "https://www.jagran.com/uttar-pradesh/lucknow-weather-update-23456789.html",
  "source": "jagran",
  "section": "weather",
  "state": "uttar-pradesh",
  "city": "lucknow",
  "date": "2026-10-06T13:21:43+05:30",
  "headline": "कल का मौसम: उत्तर प्रदेश में भारी बारिश का अलर्ट",
  "body": "लखनऊ और आसपास के इलाकों में कल सुबह से ही बादलों की आवाजाही रहेगी...",
  "keywords": ["मौसम", "बारिश", "लखनऊ"],
  "agency_flag": false,
  "content_hash": "a9f3b821...",
  "dup_of": null,
  "links": ["jagran_23450001"]
}
```

* `date` must be ISO-8601 in IST timezone (`+05:30`).
* `dup_of` is the `doc_id` of the original article if near-duplicate, otherwise `null`.
* `links` is a list of other crawled `doc_id`s found in this article's body.
* `agency_flag` is boolean (`true` if wire story).
* No author names stored.

---

## 5. Test Suite (`partwise-tests/riya/`)
* **`test_robots.py`:** Unit test comparing custom `RobotsParser` vs `urllib.robotparser` on cached `robots.txt` files from Jagran, Jansatta, Live Hindustan, and Amar Ujala.
* **`test_frontier.py`:** Verify that the min-heap strictly enforces $\ge 8.0$ seconds delay per host and front queues respect priority weights.
* **`test_normalizer.py`:** Verify URL cleaning, AMP-to-canonical conversion, and query parameter stripping.
* **`test_extractor.py`:** Verify JSON-LD extraction, IST date parsing, and absence of author names on sample HTML fixtures.
* **`test_dedup.py`:** Precision & recall on 100 labeled article pairs, plus speed comparison of exact Jaccard vs MinHash + LSH.
* **`test_format_compliance.py`:** JSON schema validation ensuring every record in `data/news.jsonl` adheres to `formats.md`.

---

## 6. Milestones & Checklist
* [ ] **Phase 1 (H1–H3):**
  - Implement `robots.py` and unit tests.
  - Build `frontier.py` skeleton and basic sitemap parser.
  - **Handoff (H3):** Generate and provide `data/news_sample_300.jsonl` (300 clean articles).
* [ ] **Phase 2 (H3–H8):**
  - Implement `extractor.py`, `normalizer.py`, and `filters.py`.
  - Start continuous 5-site crawling.
* [ ] **Phase 3 (H8–H12):**
  - Implement `dedup.py` (shingles, Jaccard, `dup_of`, `links`).
  - Monitor crawl logs and site balance.
* [ ] **Phase 4 (H12–H22):**
  - Add MinHash + LSH, adaptive recrawl (`recrawl.py`), and burst prioritization.
  - **Corpus Freeze (H18):** Lock master news corpus at 5k–12k articles.
* [ ] **Phase 5 (H22–H28):**
  - Implement `dhvani/eval/pool.py`.
  - Generate evaluation tables (dedup threshold precision/recall, MinHash vs exact speed).
* [ ] **Phase 6 (H28–H36):**
  - Write report section (crawling, robots.txt findings, deduplication).
  - Record video segment (crawler live log, robots test demo, duplicate story clusters).