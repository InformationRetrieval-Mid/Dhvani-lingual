# Architectural & Design Decisions (Riya - P1)

## Task 1: Setup, Compliance & Filtering
- **Target Sites & Blacklist:**
  - 5 primary sites (*Dainik Jagran, Navbharat Times, Live Hindustan, Amar Ujala, Aaj Tak*) and 2 backups (*Jansatta, Bhaskar*).
  - Blacklisted *BBC Hindi* (robots.txt forbids scraping/datasets) and *News18 / NDTV* (Cloudflare bot blocks).

- **Ethical Crawling & Privacy:**
  - User-Agent set to `CollegeProject_NewsBot(+https://github.com/InformationRetrieval-Mid/Dhvani-lingual; contact: ra810@snu.edu.in)`.
  - Zero author names stored anywhere in the dataset.
  - Full article text stays strictly on local machines (`data/*.jsonl` gitignored); only code and URLs go to GitHub.

- **URL Normalization & Route Filtering:**
  - Implemented scheme/domain lowercasing, stripping default ports and trailing slashes.
  - Tracking parameters (`utm_*`, `ref`, `fbclid`, `amp_js_v`) are stripped prior to frontier queueing to prevent duplicate crawl budget waste.
  - AMP URLs (`/amp/`, `?amp=1`) are mapped directly to canonical desktop versions.
  - Route filter excludes non-article routes (`/rashifal/`, `/astrology/`, `/photo-gallery/`, `/videos/`, `/live-updates/`) to avoid corpus keyword pollution.

- **Robots Parser Strategy & Test Outcome:**
  - Originally considered wrapping Python's standard `urllib.robotparser` directly.
  - **Empirical Test Result:** Testing against cached target site `robots.txt` files in [`test_robots.py`](../../../partwise-tests/riya/test_robots.py) demonstrated that `urllib.robotparser` performs literal prefix matching and fails to parse wildcard rules (`*` and `$` patterns) on *Dainik Jagran* (e.g. `/search/*`, `/state/*`) and *Amar Ujala* (e.g. `/*?utm_*`), incorrectly returning `can_fetch == True` for disallowed URLs.
  - **Decision:** Following our decision rule, we implemented custom RFC 9309 pattern-to-regex matching logic inside [`dhvani/crawl/robots.py`](../../../dhvani/crawl/robots.py) to properly handle wildcards, longest-prefix rule precedence, per-host caching, user-agent fallback (`CollegeProject_NewsBot` -> `*`), and `Sitemap:` extraction.
  - No attempt to bypass Disallow rules by altering user-agent.

---

## Task 2: Mercator Frontier & Scheduler
- **Frontier Concurrency Model (`asyncio` + `heapq`):**
  - Use a single-threaded asynchronous event loop with `asyncio` and `heapq` implemented in [`dhvani/crawl/frontier.py`](../../../dhvani/crawl/frontier.py).
  - Maintain Front queues for URL priority ($Q_0$–$Q_3$), one FIFO back queue per host for politeness, and min-heap `(next_allowed_time, entry_id, host)` for scheduling.
  - When a host becomes eligible, asynchronously dispatch its next URL; while waiting on network I/O, the event loop handles another eligible host.
  - After a request completes, reschedule that host on the heap with the required 8-second delay.
  - Theoretical scheduling across 5 hosts is $8/5 = 1.6\text{ s/request}$.
  - Single-threaded model avoids locks, thread synchronization, and concurrent file-write conflicts while overlapping network I/O.
  - **Empirical Test Result & Verification:** Validated in [`test_frontier.py`](../../../partwise-tests/riya/test_frontier.py):
    - Multi-host concurrency verified: distinct hosts dispatch concurrently with zero inter-host blocking.
    - Politeness verified: consecutive requests to the same host strictly wait $8.0\text{s}$ via deterministic simulated clock.
    - Deterministic tie-breaking: monotonic `entry_id` resolves simultaneous host eligibility in strict FIFO order.
    - Biased selection verified: 1,000-iteration simulation confirmed priority distribution ($Q_0 \approx 70.6\%$ relative ratio over $Q_1$) without starving lower queues.
    - Bounded back queues (`max_back_queue_size = 10`) eliminate head-of-line blocking during burst spikes.

---

## Task 3: Feed & Seed Management
- **Sitemap Ingestion & Conditional Discovery:**
  - Robust namespace-agnostic XML parser implemented in [`dhvani/crawl/sitemap.py`](../../../dhvani/crawl/sitemap.py) supporting standard (`<urlset>`), Google News (`<news:news>`), and sitemap index (`<sitemapindex>`) feeds.
  - Live survey confirmed working Google News sitemaps across all 5 primary sources (`jagran.com`, `navbharattimes.indiatimes.com`, `livehindustan.com`, `amarujala.com`, `aajtak.in`).
  - Added regex fallback for truncated/imperfect XML streams so network interruptions do not cause unhandled parse crashes.
  - Implemented HTTP 304 conditional request support (`If-None-Match`, `If-Modified-Since`) to eliminate redundant bandwidth consumption during polling.
  - **Empirical Test Result & Verification:** Validated in [`test_sitemap.py`](../../../partwise-tests/riya/test_sitemap.py) (7/7 tests passing including Google News fields, index discovery, conditional headers, and malformed stream resilience).

---

## Task 4: Content & Metadata Extraction
- **Article & Metadata Extraction Pipeline:**
  - 3-tier hierarchy in [`dhvani/crawl/extractor.py`](../../../dhvani/crawl/extractor.py):
    - **Tier 1 (Schema.org JSON-LD):** Primary source for `headline`, full `articleBody`, `datePublished`, `keywords`, and `articleSection`.
    - **Tier 2 (Open Graph / Meta Tags):** Used strictly to recover missing metadata (title, publication date, keywords, section). `og:description` is never used as a substitute for the full article body.
    - **Tier 3 (HTML DOM - Block-Level Fallback):**
      - **Problem:** Many Indian news CMSs (e.g. Navbharat Times `<div class="Normal">`, Amar Ujala story blocks) wrap body paragraphs in `<div>` elements rather than semantic `<p>` tags. Strict `<p>`-only extraction caused empty body false negatives.
      - **Risk (Double-Counting):** Naive iteration over `find_all(["p", "div"])` causes parent wrapper `<div>`s and child `<div>`/`<p>` tags to repeat identical text multiple times.
      - **Solution:** Decompose boilerplate elements (captions, image credits, related-content boxes, ads, social shares, bylines). Extract text from `<p>` tags and non-nested leaf `<div>` blocks (substantive length $\ge 25$ chars). When `<p>` tags provide substantive text, they take precedence; otherwise, leaf block `<div>` elements are aggregated without parent duplication.
  - **Strict IST Date Formatting:** All timestamps parsed and converted to ISO-8601 with `+05:30` offset.
  - **Zero Author Privacy Enforcement:** Clearly identified author/byline elements removed where necessary, avoiding blind wildcard deletion of classes/IDs containing "author". Record schema strictly excludes author, creator, editor, and byline fields.
  - **Conservative Geographic Tagging:** If state or city cannot be reliably identified from URL path structures, fields are explicitly set to `null` rather than guessing.
  - **Contract Validation:** Extracted articles must pass `validate_article_schema()` verifying `documentation/formats.md` compliance before being written to `data/news.jsonl`.
  - **Embedded CMS JSON Metadata Filtering:**
    - On Indian news portals (e.g. *Amar Ujala* story containers), CMSs occasionally embed raw JSON metadata blobs (e.g. `{"_id":"...", "slug":"..."}`) inside content wrapper elements.
    - Added a filter in `_extract_body_from_dom` detecting and skipping blocks starting with JSON object syntax (`text.startswith("{") and "}" in text[:100]`), keeping body prose clean.
  - **Hindi-Belt District Bureau Expansion & City Routing Conventions:**
    - Expanded `INDIAN_CITIES` from 47 tier-1 cities to cover over 120 prominent district centers across the 9 Hindi-belt states (e.g. *Basti, Ratlam, Kangra, Sikar, Pithoragarh, Alwar, Hapur, Dehradun*).
    - Added pattern recognizers for portal routing conventions: Jagran's `/<state>/<city>-city-...` slug prefix and `new-delhi` compound naming.
    - Result: City recognition on regional news increased from 33.3% (100/300) to 55.0% (165/300) on the live sample, while preserving strict `null` compliance for genuinely national, international, cricket, and state-wide policy stories.
  - **Deterministic City-to-State Derivation & Delhi Normalization:**
    - Guaranteed that no article ever has a non-null `city` with a `null` state: added `CITY_TO_STATE` mapping covering 100% of Hindi-belt cities to deterministically derive the parent state if missing from the URL.
    - Implemented Delhi city-state equivalence: articles tagged with `state: "delhi"` automatically default to `city: "delhi"` (or `"new-delhi"` if present in path), eliminating 100% of geographic field inconsistencies.
  - **Empirical Test Result & Verification:** Validated in [`test_extractor.py`](../../../partwise-tests/riya/test_extractor.py) (JSON-LD priority, meta fallback without og:description substitution, DOM block-level and leaf-div extraction without double-counting, IST date parsing, author removal, and schema compliance).

---

## Task 5: Pipeline Execution & Sample Crawl
- **Sample Handoff Sequencing & Dual Modes:**
  - Defer generating the 300-article sample (`news_sample_300.jsonl` for H3) until initial extractor, normalizer, and crawler pipeline are complete.
  - Implemented dual operational modes:
    - Dedicated `--sample` mode stopping immediately after 300 valid articles (~8 minutes runtime) to provide the H3 deliverable without waiting for the full 2.2-hour corpus.
    - Normal mode crawling toward `--max-articles` (default 5,000) while auto-saving the first 300 articles snapshot simultaneously to `data/news_sample_300.jsonl` upon reaching article #300.

- **Streaming JSONL Writer & Checkpointing:**
  - Single-threaded asynchronous pipeline streams validated JSON lines directly to disk with immediate `.flush()` after every record, preventing data loss on unexpected termination.
  - Tracks in-memory `seen_doc_ids` to eliminate intra-session duplicate writes.

- **Anti-Bot, WAF & Error Resilience Policies:**
  - **HTTP 429 (Rate Limit):** Doubles per-host delay exponentially ($8.0\text{s} \to 16.0\text{s} \to 32.0\text{s} \to 64.0\text{s}$) and reschedules the host rather than crashing the crawler.
  - **HTTP 403 & CAPTCHA Challenges:** Cloudflare/Akamai bot challenge signatures immediately disable the affected host for the current crawl session, preventing further requests that could trigger hard IP bans.
  - **HTTP 5xx & Network Timeouts:** Transient failures retried up to 2 times with exponential backoff before dropping the URL.
  - **Strict Politeness Rescheduling:** `frontier.complete_request(host, delay=eff_delay)` is executed in a strict `finally` block, ensuring no host is orphaned in-flight regardless of fetch or extraction failure.

- **Dynamic Per-Host Delay Scheduling (`frontier.py` Integration):**
  - Extended `frontier.complete_request(host, delay=eff_delay)` to accept an optional custom delay parameter, allowing `crawler.py` to reschedule rate-limited hosts with backed-off intervals while preserving the default 8.0s delay for all healthy hosts.

- **Discovered-Link Harvesting:**
  - Extracted in-body hyperlinks are normalized via `normalizer.py`, filtered via `filters.py`, deduplicated against `frontier.seen_urls`, and pushed into Frontier Front Queue $Q_2$ (In-article hyperlinks, 10% sampling weight), preventing link discoveries from bypassing polite crawling gates.

- **Native Async Test Harness (Portable Verification):**
  - Replaced `@pytest.mark.asyncio` annotations with standard library `asyncio.run(_test())` coroutine execution, eliminating external pytest plugin dependencies and guaranteeing 100% portable test execution.
  - Empirical verification: 9/9 crawler unit tests passing in 2.2s in [`test_crawler.py`](../../../partwise-tests/riya/test_crawler.py).

- **Head-Of-Line (HOL) Starvation Prevention & Multi-Source Queue Balancing:**
  - *Symptom:* During live crawl runs, articles were retrieved exclusively from a single source (*Dainik Jagran*), starving the other 4 sources (*NBT, Live Hindustan, Amar Ujala, Aaj Tak*) despite successful seed discovery.
  - *Root Cause 1 (Sequential Sitemap Ingestion & Front Queue HOL):* Seeds were originally enqueued per-source sequentially. Jagran URLs filled the head of $Q_1$. In `_refill_back_queues()`, when Jagran's back queue reached capacity (`max_back_queue_size = 10`), a premature `break` terminated refills for all other hosts in the queue.
  - *Fix 1 (Frontier Queue Rotation):* Replaced the refill loop `break` with `q.rotate(-1)` when a host's back queue is full, rotating the full host's URL to the tail so downstream candidate hosts are evaluated without blocking.
  - *Fix 2 (Round-Robin Seed Interleaving):* In `bootstrap_seeds()`, sitemap URLs across all active sources are interleaved round-robin into $Q_1$, ensuring equal representation across sources from crawl startup.
  - *Root Cause 2 (Heap Duplication & Delay Collapse):* `complete_request()` previously called `_refill_back_queues()` (which scheduled the host on the heap) and then pushed the host onto the heap a second time unconditionally. Duplicate entries with expired timestamps bypassed the 8.0s politeness delay.
  - *Fix 3 (Single-Entry Heap Invariant):* Rescheduled the host on the min-heap strictly once with `hosts_in_heap` tracking before refilling back queues, guaranteeing at most one heap entry per host at all times.
  - *Root Cause 3 (Bulk Ingestion Queue Spin Stall):* After discovering ~10,000 URLs across sitemaps, transferring URLs into back queues spun through unneeded rotations (`O(len(q))` per call) when back queues were already saturated, causing an apparent freeze at startup.
  - *Fix 4 (State-Driven Back Queue Saturation Detection):* Rather than arbitrary constant skips, `_refill_back_queues()` explicitly computes `hungry_hosts = {h for h, bq in self.back_queues.items() if len(bq) < self.max_back_queue_size}`. If `not hungry_hosts and len(self.back_queues) >= 5`, it terminates in $O(1)$ time with 0 rotations. During rotation, skips are dynamically bounded by known active hosts (`consecutive_skips >= max(len(self.back_queues), 10)`), completely eliminating heuristic magic numbers while preventing bootstrap starvation.
  - *Root Cause 4 (CAPTCHA False Positives on CSS Stylesheets):* The initial signature list included generic substrings like `"recaptcha"`. Normal article pages on *Live Hindustan* containing `.grecaptcha-badge` in their `<style>` blocks triggered false-positive bot challenge detections on HTTP 200 responses, erroneously disabling healthy domains for the entire session.
  - *Fix 5 (High-Precision Interception Signatures & Content Guards):* Removed ambiguous substrings from `CAPTCHA_SIGNATURES`, narrowed down to verified challenge page markers (Cloudflare `cf-challenge-running`, `<title>Just a moment...</title>`), and added structural content guards ensuring pages with valid `schema.org/NewsArticle` JSON-LD or `<article>` tags are never classified as interstitial blocks.

---

## Task 6: Deduplication & Story Clustering
- **Deduplication & Story Clustering (MinHash + LSH):**
  - 3-tier pipeline: Exact MD5 `content_hash` -> 4-word shingles -> 64-permutation MinHash with LSH ($b=16, r=4$) for scalable candidate bucketing.
  - 4-word shingles grounded in Broder (1997) adapted for Hindi syntax (prevents collisions on high-frequency postpositions like *का, की, के, में, से*).
  - $\pm 24$-hour temporal window for clustering syndicated wire stories (PTI, ANI, Bhasha).
  - Earliest published story marked as canonical root (`dup_of: null`), later reprints set `dup_of: "<earliest_doc_id>"`.
  - Wire agency signatures detected to set `agency_flag: true`.
  - Jaccard cutoff ($0.70$) will be calibrated on 100 labeled article pairs once real articles are crawled.

---

## Task 7: Adaptive Recrawling & Event Prioritization
- **Adaptive Recrawling & Freshness (EWMA):**
  - Track source change rate using EWMA: $\lambda_s^{(t)} = \alpha \cdot \frac{\Delta N}{\Delta t} + (1 - \alpha) \cdot \lambda_s^{(t-1)}$ with $\alpha = 0.3$.
  - Grounded in Cho & Garcia-Molina change-rate model and RFC 6298 network smoothing standards.
  - Dynamic polling interval $\tau_s \in [30\text{ minutes}, 6\text{ hours}]$, reflecting newsroom publishing cycles.
  - Use conditional HTTP headers (`If-Modified-Since`, `ETag`) to terminate early on unchanged feeds (`304 Not Modified`).

- **Event / Burst-Aware Prioritization:**
  - Detect breaking news surges using a rolling 60-minute window against a 6-hour baseline: $\text{BurstScore} = \frac{\text{Count}_{1\text{h}}}{\text{MovingAvg}_{6\text{h}} + 1} > 2.0$.
  - Biased random sampling across Front Queues: $P(Q_0)=0.60, P(Q_1)=0.25, P(Q_2)=0.10, P(Q_3)=0.05$.
  - Following Mercator (Heydon & Najork, 1999), biased sampling ensures starvation-free prioritization without blocking routine sitemaps during bursts.
  - Politeness strictly enforced per-host at back queues and min-heap (8.0s per host).
  - Burst threshold ($2.0$) and queue weights ($60\%$) will be calibrated via sensitivity tests once live data is flowing.

---

## Task 8: Shared Evaluation Tooling
- **Shared Tooling & Downstream Support (`eval/pool.py`):**
  - Implementation of TREC run pooling reading `qid Q0 doc_id rank score run_name` across team runs.
  - Top-$k$ depth pooling ($k=10$ or $20$) to produce deduplicated judgment pool sheets (`need_id 0 doc_id rel`).

---

## Optional Enhancement & Research Grounding
- **Semantic Prioritization Grounding:**
  - Added academic reference for retrieval-agnostic corpus utility: [Neural Prioritisation for Web Crawling](https://eprints.gla.ac.uk/359292/) (Macdonald et al., Glasgow).
