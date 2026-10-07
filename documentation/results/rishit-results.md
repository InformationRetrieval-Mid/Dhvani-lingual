# Rishit's results

Results for ranking, the cross-lingual layer and evaluation. Each section says which corpus, queries and settings it used, so early numbers and final numbers don't get mixed up. Plots go in `documentation/figures/` as `rishit-*.png`.

| Section | Status |
|---|---|
| Speed-ups vs exact lnc.ltc | Frozen corpus (5,000 articles) |
| Stemming: none vs light vs auto | Waiting for judgments |
| Translation off vs on | Waiting for judgments |
| lnc.ltc vs BM25 vs net score | Waiting for judgments |
| Stop words, idf and Zipf | Frozen corpus (5,000 articles) |
| Dense re-ranking vs sparse only | Waiting for judgments |
| Rank fusion (RRF) vs single rankers | Waiting for judgments |
| Sanity check without judgments | Frozen corpus (5,000 articles) |
| Query difficulty hint | Frozen corpus (5,000 articles) |
| Learning-to-rank | Waiting for judgments |
| Wins and losses | Waiting for judgments |

## Speed-ups vs exact lnc.ltc

> **Final corpus.** These are on the frozen corpus: Riya's full crawl with its one repeated article removed, 5,000 articles. It wasn't cleaned further, so it still has HTML in 249 bodies, 106 astrology pages and about 50 section pages saved as articles; those are listed as limitations.

- **Corpus:** the frozen corpus, `data/news.jsonl` (Riya's `news_dedup.jsonl`, 5,001 lines, minus the one article saved twice: 5,000 articles), mostly from 5 to 7 Oct; no-stemming index, 83,560 distinct words
- **Queries:** 64, all four forms of Rishit's R01 to R08 and Viraja's V01 to V08, through the full query pipeline (Viraja's `build_query`, phonetic variants, translation)
- **k:** 10
- **Date run:** 7 Oct, rerun after Viraja's rare-spelling fix
- **How to rerun:** `speedup_table()` in `dhvani/eval/experiments.py`

"Scored" is the average share of the articles sharing a query word that each method actually scored (lower is faster). "Kept" is the average share of the exact lnc.ltc top 10 that the method also returned (higher is closer to exact).

| Method | Scored | Kept |
|---|---|---|
| Index elimination | 0.01 | 0.73 |
| Champion lists, r = 2 | 0.06 | 0.38 |
| Champion lists, r = 5 | 0.03 | 0.67 |
| Champion lists, r = 10 | 0.05 | 0.87 |
| Champion lists, r = 50 | 0.18 | 1.00 |
| Recent-news tiers | 0.95 | 0.97 |
| Cluster pruning, b = 1 | 0.03 | 0.27 |
| Cluster pruning, b = 3 | 0.07 | 0.41 |
| Impact-ordered, first 20 per word | 0.09 | 0.65 |
| Impact-ordered, first 50 per word | 0.18 | 0.80 |
| Impact-ordered, weight at least 0.5 x best | 0.36 | 0.70 |

**What it shows**
- **Champion lists give the best trade-off.** With r = 50 they score under a fifth of the candidates and still return exactly the full top 10. r = 10 keeps 87% while scoring only 5%. With r = 2 the lists are often too short for 10 results, so it falls back to the full postings more, which is why it scores more than r = 5.
- **Impact-ordered postings come second.** Reading the first 50 articles of each word's list scores the same 18% as champion lists with r = 50 but keeps 80%, because the cut-off isn't tuned in advance per word.
- **Index elimination is the cheapest that's still usable.** Dropping words like के and में and asking for most of the remaining words scores 1% and keeps 73%.
- **Cluster pruning is fast but loses the most.** One cluster scores 3% and keeps 27%. Articles about one story end up spread across several clusters, so the closest leader only covers part of them.
- **Recent-news tiers barely cut anything.** Almost all articles are from the last two days (3,150 from 7 Oct alone), so tier 0 is nearly the whole corpus.

### Earlier run on the 300-article sample

Same queries and k on Riya's 300-article sample, kept for comparison. With so few articles every method looked better, which is why the speed-ups had to be checked on the frozen corpus.

| Method | Scored | Kept |
|---|---|---|
| Index elimination | 0.21 | 0.72 |
| Champion lists, r = 5 | 0.27 | 0.93 |
| Champion lists, r = 10 | 0.37 | 0.99 |
| Cluster pruning, b = 1 | 0.15 | 0.28 |
| Impact-ordered, first 20 per word | 0.51 | 0.94 |

## Stop words, idf and Zipf

> **Final corpus.** Same frozen 5,000-article corpus as above.

- **Corpus:** 5,000 articles, no-stemming index, 83,560 distinct words, 40,255 of them seen only once
- **How to rerun:** `term_stats()`, `stop_words()` and `zipf_fit()` in `dhvani/eval/corpus_stats.py`
- **Plots:** `documentation/figures/rishit-zipf.png`, `documentation/figures/rishit-idf-histogram.png`

The 15 most widespread words, by document frequency (df), with collection frequency (cf) and idf = log10(N / df):

| Word | df | cf | idf |
|---|---|---|---|
| के | 4,926 | 92,206 | 0.006 |
| की | 4,903 | 66,394 | 0.009 |
| में | 4,886 | 74,879 | 0.010 |
| से | 4,821 | 44,687 | 0.016 |
| का | 4,806 | 36,013 | 0.017 |
| और | 4,789 | 47,396 | 0.019 |
| को | 4,788 | 41,178 | 0.019 |
| पर | 4,678 | 31,069 | 0.029 |
| है | 4,461 | 55,111 | 0.050 |
| ने | 4,369 | 32,794 | 0.059 |
| भी | 4,146 | 18,068 | 0.081 |
| लिए | 4,069 | 14,592 | 0.089 |
| हैं | 3,684 | 19,196 | 0.133 |
| किया | 3,675 | 11,436 | 0.134 |
| कि | 3,654 | 17,882 | 0.136 |

**What it shows**
- **The stop words come straight out of the data.** The top 15 by df are all Hindi postpositions, conjunctions and auxiliaries. के is in 4,926 of 5,000 articles, so its idf is almost 0 and it barely affects lnc.ltc even without a stop list. That's why the ranker keeps them instead of removing them: idf already does the job, and phrase queries like "भूकंप के झटके" still match exactly.
- **Zipf's law holds for the frequent words.** Over the 1,000 most frequent words the slope is -0.90, close to the -1 of Zipf's law. The fit over all 83,560 words gives -1.45 because 40,255 words appear only once (names, numbers, typos), which drags the tail down. On the plot the line follows the middle of the curve and overshoots the very top, where a handful of function words take a large share of all tokens.

## Query difficulty

> **Frozen corpus, no judgments yet.** Same 5,000-article corpus. Whether flagged queries really do worse can only be checked once there are judgments.

- **Queries:** the 64 needs queries (R01 to R08, V01 to V08, four forms each), plus a handful of deliberately vague ones
- **How to rerun:** `predict()` in `dhvani/rank/difficulty.py`

| Signal | Needs queries | Vague queries |
|---|---|---|
| Specificity (highest per-word idf) | lowest 1.24, middle half 1.9 to 2.4 | news 0.63, kya hua 0.56, बड़ी खबर 0.81, के में 0.01, india 0.69 |
| Clarity (bits) | 1.11 to 1.82 | news 3.02, के में 1.27 |

**What it shows so far**
- **Specificity separates them cleanly.** Every needs query has a word with idf above 1.2; every vague query stays below 1.0. The threshold sits at 1.0.
- **Clarity doesn't work here.** It stays in a narrow band for real queries, and "news" scores highest of all because its top results are near-identical listing pages. It's kept as a reported number only.
- **6 of the 64 needs queries are flagged** (11 before Viraja's rare-spelling fix), all because only the "any word" stage matched: Hinglish or messy forms of V01, V02, V04, V05 and V08. Those are the forms where the phonetic layer still doesn't find every word, so the flag points at real weak spots.

## Sanity check without judgments

> **Frozen corpus, no judgments needed.** These come straight from the run files: 64 queries (R01 to R08, V01 to V08, four forms each), 4 stemming modes x 4 rankers, top 10.

- **How to rerun:** `python -m dhvani.eval.experiments --out data/eval/full`, then `python -m dhvani.eval.sanity`

### Do the four forms of a need find the same articles?
Share of the Hindi form's top 10 that each other form also returns, averaged over the 16 needs.

| Run | Hinglish | Messy | English |
|---|---|---|---|
| none, lnc.ltc | 0.41 | 0.41 | 0.36 |
| none, BM25 | **0.47** | 0.45 | 0.39 |
| none, net score | 0.38 | 0.28 | 0.24 |
| none, fusion | **0.47** | 0.45 | 0.34 |
| light, BM25 | 0.45 | **0.47** | **0.40** |
| light, fusion | **0.47** | **0.47** | 0.38 |
| light, net score | 0.36 | 0.31 | 0.24 |
| auto, BM25 | **0.47** | 0.45 | 0.39 |
| aggr, BM25 | 0.43 | 0.45 | 0.38 |

English form with translation off vs on (no stemming, net score): **0.19 → 0.24**.

Before Viraja's rare-spelling fix (same day) these were 0.24 to 0.38 for Hinglish, 0.20 to 0.33 for messy and 0.19 to 0.32 for English, so the fix lifted agreement by about 0.1 across the board.

### Do the systems agree with each other?
Share of the same top 10 (overlap) and Kendall's tau on the order of the articles both returned.

| Pair | Overlap | Tau |
|---|---|---|
| lnc.ltc vs BM25 | 0.86 | 0.73 |
| lnc.ltc vs fusion | 0.84 | 0.63 |
| BM25 vs net score | 0.61 | 0.52 |
| lnc.ltc vs net score | 0.61 | 0.51 |
| no stemming vs light (net) | 0.88 | 0.91 |
| no stemming vs aggressive (net) | 0.90 | 0.93 |
| no stemming vs auto (net) | 0.99 | 0.99 |

**What it shows**
- **The forms agree less than the demo queries suggest.** About 40 to 47% of the Hindi form's top 10 comes back for the Hinglish and messy forms with BM25 or fusion, and up to 40% for English. Words that still don't map to the right Hindi spelling (देल्ही for delhi, एयर for iyer) or are missing from the dictionary send the search elsewhere. This is the main limitation to report.
- **Translation helps English queries.** Agreement with the Hindi form goes from 0.19 to 0.24 with the dictionary on.
- **BM25 and fusion agree best across forms**, so they're the most robust to how the query is written; the net score agrees least, because its zone and authority boosts favour different articles per form.
- **lnc.ltc and BM25 mostly agree; the net score differs most**, because zones, proximity and authority reorder a lot. Judgments will say whether that's better or worse.
- **Auto stemming is almost the same as no stemming** on the frozen corpus (0.99), because its candidates were learned on the 300-article sample and few of them apply to 5,000 articles.
