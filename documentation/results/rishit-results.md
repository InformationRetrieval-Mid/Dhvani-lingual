# Rishit's results

Results for ranking, the cross-lingual layer and evaluation. Each section says which corpus, queries and settings it used, so early numbers and final numbers don't get mixed up. Plots go in `documentation/figures/` as `rishit-*.png`.

| Section | Status |
|---|---|
| Speed-ups vs exact lnc.ltc | Early numbers (300-article sample) |
| Stemming: none vs light vs auto | Waiting for judgments |
| Translation off vs on | Waiting for judgments |
| lnc.ltc vs BM25 vs net score | Waiting for judgments |
| Stop words, idf and Zipf | Waiting for the full crawl |
| Learning-to-rank | Waiting for judgments |
| Wins and losses | Waiting for judgments |

## Speed-ups vs exact lnc.ltc

> **Early numbers.** These are from Riya's 300-article sample, not the frozen corpus. They'll be redone on the full crawl and may change a lot, since the speed-ups matter more as the collection grows.

- **Corpus:** Riya's 300-article sample (`news_sample_300.jsonl`, articles from 6 and 7 Oct), no-stemming index
- **Queries:** 64, all four forms of Rishit's R01 to R08 and Viraja's V01 to V08, through the full query pipeline (Viraja's `build_query`, phonetic variants, translation)
- **k:** 10
- **Date run:** 7 Oct
- **How to rerun:** `speedup_table()` in `dhvani/eval/experiments.py`

"Scored" is the average share of the articles sharing a query word that each method actually scored (lower is faster). "Kept" is the average share of the exact lnc.ltc top 10 that the method also returned (higher is closer to exact).

| Method | Scored | Kept |
|---|---|---|
| Index elimination | 0.21 | 0.72 |
| Champion lists, r = 2 | 0.19 | 0.68 |
| Champion lists, r = 5 | 0.27 | 0.93 |
| Champion lists, r = 10 | 0.37 | 0.99 |
| Champion lists, r = 50 | 0.70 | 1.00 |
| Recent-news tiers | 1.00 | 1.00 |
| Cluster pruning, b = 1 | 0.15 | 0.28 |
| Cluster pruning, b = 3 | 0.26 | 0.39 |
| Impact-ordered, first 20 per word | 0.51 | 0.94 |
| Impact-ordered, first 50 per word | 0.70 | 0.99 |
| Impact-ordered, weight at least 0.5 x best | 0.87 | 0.87 |

**What it shows so far**
- **Champion lists give the best trade-off.** With r = 5 they score about a quarter of the candidates and keep 93% of the exact top 10. r = 10 is almost exact at 37%.
- **Cluster pruning is the fastest but loses the most.** One cluster scores only 15% and keeps 28% of the top 10. Articles about one news story end up spread over several clusters, so the closest leader only covers part of them.
- **Index elimination sits in between.** Dropping low-idf words like के and में and asking for most of the query words keeps 72% while scoring 21%.
- **Impact-ordered postings are close behind champion lists.** Reading only the first 20 articles of each word's list (44% of the postings) keeps 94% of the top 10. Unlike champion lists nothing is fixed in advance, so the cut-off can change per query.
- **Stopping by weight barely helps on news.** Inside one word's list the weights are close together, so a floor of half the best weight still reads 78% of the postings and loses more of the top 10 than stopping after 20 articles.
- **Recent-news tiers do nothing here.** All 300 articles are from the last two days, so everything is in tier 0. On the full crawl, with older articles, this should change.
