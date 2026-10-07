# Rishit's results

Results for ranking, the cross-lingual layer and evaluation. Each section says which corpus, queries and settings it used, so early numbers and final numbers don't get mixed up. Plots go in `documentation/figures/` as `rishit-*.png`.

| Section | Status |
|---|---|
| Speed-ups vs exact lnc.ltc | Riya's full crawl, before the freeze (5,000 articles) |
| Stemming: none vs light vs auto | Waiting for judgments |
| Translation off vs on | Waiting for judgments |
| lnc.ltc vs BM25 vs net score | Waiting for judgments |
| Stop words, idf and Zipf | Riya's full crawl, before the freeze (5,000 articles) |
| Dense re-ranking vs sparse only | Waiting for judgments |
| Learning-to-rank | Waiting for judgments |
| Wins and losses | Waiting for judgments |

## Speed-ups vs exact lnc.ltc

> **Before the freeze.** These are from Riya's full crawl (5,000 articles), but the corpus hasn't been cleaned and frozen yet: it still has HTML in some bodies, astrology pages and section pages saved as articles. The final numbers will be rerun on the frozen corpus.

- **Corpus:** Riya's full crawl (`news_dedup.jsonl`, 5,001 lines with one article saved twice, so 5,000 articles), mostly from 5 to 7 Oct; no-stemming index, 83,560 distinct words
- **Queries:** 64, all four forms of Rishit's R01 to R08 and Viraja's V01 to V08, through the full query pipeline (Viraja's `build_query`, phonetic variants, translation)
- **k:** 10
- **Date run:** 7 Oct
- **How to rerun:** `speedup_table()` in `dhvani/eval/experiments.py`

"Scored" is the average share of the articles sharing a query word that each method actually scored (lower is faster). "Kept" is the average share of the exact lnc.ltc top 10 that the method also returned (higher is closer to exact).

| Method | Scored | Kept |
|---|---|---|
| Index elimination | 0.02 | 0.60 |
| Champion lists, r = 2 | 0.02 | 0.39 |
| Champion lists, r = 5 | 0.04 | 0.71 |
| Champion lists, r = 10 | 0.07 | 0.89 |
| Champion lists, r = 50 | 0.21 | 1.00 |
| Recent-news tiers | 0.95 | 0.98 |
| Cluster pruning, b = 1 | 0.03 | 0.23 |
| Cluster pruning, b = 3 | 0.07 | 0.35 |
| Impact-ordered, first 20 per word | 0.11 | 0.70 |
| Impact-ordered, first 50 per word | 0.21 | 0.83 |
| Impact-ordered, weight at least 0.5 x best | 0.34 | 0.70 |

**What it shows**
- **Champion lists give the best trade-off.** With r = 50 they score a fifth of the candidates and still return exactly the full top 10. r = 10 keeps 89% while scoring only 7%.
- **Impact-ordered postings come second.** Reading the first 50 articles of each word's list scores the same 21% as champion lists with r = 50 but keeps 83%, because the cut-off isn't tuned in advance per word.
- **Index elimination is the cheapest that's still usable.** Dropping words like के and में and asking for most of the remaining words scores 2% and keeps 60%.
- **Cluster pruning is fast but loses the most.** One cluster scores 3% and keeps 23%. Articles about one story end up spread across several clusters, so the closest leader only covers part of them.
- **Recent-news tiers barely cut anything.** Almost all articles are from the last two days (3,150 from 7 Oct alone), so tier 0 is nearly the whole corpus.

### Earlier run on the 300-article sample

Same queries and k on Riya's 300-article sample, kept for comparison. With so few articles every method looked better, which is why the speed-ups had to be checked on the full crawl.

| Method | Scored | Kept |
|---|---|---|
| Index elimination | 0.21 | 0.72 |
| Champion lists, r = 5 | 0.27 | 0.93 |
| Champion lists, r = 10 | 0.37 | 0.99 |
| Cluster pruning, b = 1 | 0.15 | 0.28 |
| Impact-ordered, first 20 per word | 0.51 | 0.94 |

## Stop words, idf and Zipf

> **Before the freeze.** Same 5,000-article corpus as above. The final numbers will be rerun on the frozen corpus.

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
