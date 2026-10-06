# Architectural & Design Decisions (Riya - P1)

- **Robots Parser Strategy & Test Outcome:**
  - Originally considered wrapping Python's standard `urllib.robotparser` directly.
  - **Empirical Test Result:** Testing against cached target site `robots.txt` files in [`test_robots.py`](../../../partwise-tests/riya/test_robots.py) demonstrated that `urllib.robotparser` performs literal prefix matching and fails to parse wildcard rules (`*` and `$` patterns) on *Dainik Jagran* (e.g. `/search/*`, `/state/*`) and *Amar Ujala* (e.g. `/*?utm_*`), incorrectly returning `can_fetch == True` for disallowed URLs.
  - **Decision:** Following our decision rule, we implemented custom RFC 9309 pattern-to-regex matching logic inside [`dhvani/crawl/robots.py`](../../../dhvani/crawl/robots.py) to properly handle wildcards, longest-prefix rule precedence, per-host caching, user-agent fallback (`CollegeProject_NewsBot` -> `*`), and `Sitemap:` extraction.
  - No attempt to bypass Disallow rules by altering user-agent.

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

- **Sample Handoff Sequencing:**
  - Defer generating the 300-article sample (`news_sample_300.jsonl` for H3) until initial extractor, normalizer, and crawler pipeline are complete.

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

- **Deduplication & Story Clustering (MinHash + LSH):**
  - 3-tier pipeline: Exact MD5 `content_hash` -> 4-word shingles -> 64-permutation MinHash with LSH ($b=16, r=4$) for scalable candidate bucketing.
  - 4-word shingles grounded in Broder (1997) adapted for Hindi syntax (prevents collisions on high-frequency postpositions like *का, की, के, में, से*).
  - $\pm 24$-hour temporal window for clustering syndicated wire stories (PTI, ANI, Bhasha).
  - Earliest published story marked as canonical root (`dup_of: null`), later reprints set `dup_of: "<earliest_doc_id>"`.
  - Wire agency signatures detected to set `agency_flag: true`.
  - Jaccard cutoff ($0.70$) will be calibrated on 100 labeled article pairs once real articles are crawled.

- **Target Sites & Blacklist:**
  - 5 primary sites (*Dainik Jagran, Navbharat Times, Live Hindustan, Amar Ujala, Aaj Tak*) and 2 backups (*Jansatta, Bhaskar*).
  - Blacklisted *BBC Hindi* (robots.txt forbids scraping/datasets) and *News18 / NDTV* (Cloudflare bot blocks).

- **Ethical Crawling & Privacy:**
  - User-Agent set to `CollegeProject_NewsBot(+https://github.com/InformationRetrieval-Mid/Dhvani-lingual; contact: ra810@snu.edu.in)`.
  - Zero author names stored anywhere in the dataset.
  - Full article text stays strictly on local machines (`data/*.jsonl` gitignored); only code and URLs go to GitHub.

- **Semantic Prioritization Grounding:**
  - Added academic reference for retrieval-agnostic corpus utility: [Neural Prioritisation for Web Crawling](https://eprints.gla.ac.uk/359292/) (Macdonald et al., Glasgow).
