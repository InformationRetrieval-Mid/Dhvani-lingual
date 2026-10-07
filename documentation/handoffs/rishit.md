# Handoff

What I've built, where it lives, and how the rest of the team can use it. The module notes below only cover work that's committed on the `rishit` branch; work in progress and teammates' status are tracked in `documentation/to-dos/todo.md`, and the reasons behind choices are in `documentation/decisions.md`.

Last updated: 7 Oct, after adding champion lists

## Start here (for anyone, or any AI tool, picking this up)

**The project.** Dhvani is a Hindi + Hinglish news search engine for CSD358 Track 5 (multilingual and Indic-language search). Queries can be Hindi, Hinglish (Roman-script Hindi, any spelling), English or a mix, and every search runs on three indexes side by side: no stemming, stemming and auto. The full plan is `documentation/dhvani-plan.md` and the shared data formats are `documentation/formats.md`.

**Who owns what.**
| Person | Branch | Part | Code |
|---|---|---|---|
| Riya | `riya` | Crawler and corpus | `dhvani/crawl/`, `dhvani/eval/pool.py` |
| Dhrithi | `Dhrithi` | Text processing and indexes | top-level `text/`, `index/`, `scripts/`, tests in top-level `tests/` |
| Viraja | `Viraja` | Hinglish phonetic layer | `dhvani/query/` |
| Rishit | `rishit` | Ranking, cross-lingual layer, evaluation, app | `dhvani/rank/`, `dhvani/eval/` (except `pool.py`), `app/` |

Each person commits to their own branch. Nothing has been merged into `main` yet, so `main` only has the plan and the formats.

**Setup.**
```bash
python3 -m venv .venv
.venv/bin/pip install regex streamlit pytest      # matplotlib too, if you want the plots
.venv/bin/python -m pytest partwise-tests/rishit -q
.venv/bin/streamlit run app/streamlit_app.py
```

**Rules for working in this repo.**
- Commits go under the person who did the work. No AI co-author lines or tool names in commit messages.
- Small commits with short, plain messages. Ask Rishit before pushing anything from this branch.
- With every commit on this branch, update this handoff, the to-do list and the decisions log.
- No em dashes in the docs; keep the writing plain.
- Article text never goes in git. Only the top-level `data/` folder is ignored, so crawled articles, indexes and downloads go there.
- Don't change a shared format in `formats.md` without telling the group.

**Where things stand right now.** Everything here runs on the 20-article sample index with exact-match queries plus English translation. The real pieces exist on teammates' branches but aren't plugged in yet:
- Viraja's `build_query(raw, index=None, costs=None)` in `dhvani/query/build.py` is ready to replace `query_stub.exact_query`.
- Dhrithi's `Index.load(mode)` in `index/positional.py` has modes none, light and aggr. Its `doc_norm` is empty and `meta` doesn't keep `links` or `city` yet; there's no `auto` mode yet.
- Riya's 300-article sample is `data/news_sample_300.jsonl` on her branch, with every field in `formats.md`.

## My part
Ranking, the cross-lingual layer, evaluation, and the app. Code lives in `dhvani/rank/`, `dhvani/eval/` and `app/`, tests in `partwise-tests/rishit/`.

## Committed so far

| Commit | What it does |
|---|---|
| `574e7c8` set up the dhvani package and a sample index to build ranking on | `dhvani` package, `.gitignore`, and `dhvani/rank/sample_index.py` |
| `9a8a1ba` lnc.ltc scoring with heap top-k | `dhvani/rank/vsm.py` and `dhvani/rank/query_stub.py` |
| `23cbb1a` net score with zone weights, proximity and recency | `dhvani/rank/scoring.py` |
| `0009026` added bm25 | `dhvani/rank/bm25.py` |
| `e1958f1` filters for source, section, state and date | `dhvani/rank/filters.py`, plus a `doc_filter` option on all three rankers |
| `728c3e4` sample index keeps article text for display | `SampleIndex.articles` holds headline and body |
| `43f3c50` first version of the streamlit app with the three stemming columns | `app/streamlit_app.py` |
| `896eab0` highlighted query words and snippets in the app | best-matching sentence for each result, matched words coloured |
| `6d88458` match chips, filters and score breakdown in the app | rest of `app/streamlit_app.py` |
| `4c95b31` redesigned the app in an apple style | new look for `app/streamlit_app.py` |
| `202fac6` search from the terminal with --explain | `app/cli.py` |
| `bdd6b29` query parser that tries the exact phrase first | `dhvani/rank/parser.py` |
| `6063301` parser stages shown in the app and the cli | `app/streamlit_app.py`, `app/cli.py` |
| `8cc6b07` cross-lingual layer for english queries | `dhvani/rank/xling.py` and the English to Hindi news dictionary |
| `69faf76` translation switch in the app and cli | `app/streamlit_app.py`, `app/cli.py` |
| `561d129` metrics for P@k, R@k, MAP, nDCG and PR curves | `dhvani/eval/metrics.py` |
| `a39e4fa` experiment runner with the stemming comparison | `dhvani/eval/experiments.py`, sample queries and judgments |
| `ae172cd` stop words, idf and zipf analysis | `dhvani/eval/corpus_stats.py`, a no-idf option in `vsm.py` |
| `fea28e2` feedback match type in the app and parser | `app/streamlit_app.py`, `dhvani/rank/parser.py` |
| `60ac8d1` index elimination: skip low-idf words and score only real contenders | `dhvani/rank/speedups.py` |
| champion lists: precompute each term's top articles and score only those | `dhvani/rank/speedups.py` |

## How to use it

**Sample index** (`dhvani/rank/sample_index.py`)
20 hand-written Hindi articles across weather, sports, politics, business, crime, education, entertainment and national news. It has the same methods as the real index in `formats.md`: `postings(term, zone)`, `df(term)`, `N`, `vocab`, `doc_norm`, `meta`. Two articles are the same wire story and a few link to each other, for duplicate and PageRank testing.
```python
from dhvani.rank.sample_index import SampleIndex
idx = SampleIndex.load("none")
```

**Query stub** (`dhvani/rank/query_stub.py`)
Builds the query object from `formats.md` with exact matches only. It stands in for Viraja's `dhvani.query.build.build_query`, which is finished on her branch and has the same output shape; swap the import once the branches are merged.
```python
from dhvani.rank.query_stub import exact_query
q = exact_query("दिल्ली बारिश")
```

**lnc.ltc** (`dhvani/rank/vsm.py`)
```python
from dhvani.rank.vsm import search
search(q, idx, k=10)   # [(doc_id, score, {term: contribution})]
```

**Net score** (`dhvani/rank/scoring.py`)
cosine + 0.2 x zone + 0.1 x proximity + 0.1 x recency. The explain dict has every part.
```python
from dhvani.rank.scoring import rank
rank(q, idx, k=10)     # [(doc_id, net, {"cosine", "terms", "zone", "proximity", "recency", "net"})]
```

**BM25** (`dhvani/rank/bm25.py`)
k1 = 1.2, b = 0.75, idf that stays positive, optional headline boost.
```python
from dhvani.rank.bm25 import search_bm25
search_bm25(q, idx, k=10)
```

**Filters** (`dhvani/rank/filters.py`)
Source, section, state and date range. Every filter that's set has to match, and they're applied before the top K is picked, so a filtered search still gets its best results.
```python
from dhvani.rank.filters import make_filter
f = make_filter(idx, sources=["jagran"], states=["delhi"], date_from="2026-10-05")
rank(q, idx, k=10, doc_filter=f)     # same for search() and search_bm25()
```

**Article text** (`SampleIndex.articles`)
`idx.articles[doc_id]` gives `{"headline", "body"}` for showing results. The real system will read this from the article file.

**The app** (`app/streamlit_app.py`)
Styled after Apple's design guidelines. A translucent bar sits at the top, and a big centred search field has suggestion pills under it. A segmented control picks the ranking model (net score, lnc.ltc or BM25), and a Filters popover next to it holds newspaper, section, state, results per column and date range. Results show in three grouped lists side by side: no stemming, stemming and auto. Each row shows the paper, section, place, date and score, the headline and best-matching sentence with matched words tinted by match type, chips for how each word matched (exact, phonetic, translated, or feedback for Rocchio terms), an "Only here" tag if the result isn't in the other columns, a small label for the parser stage that matched it, and a "Score details" disclosure with the full breakdown. The Filters popover has a "Smart query parsing" switch and a "Translate English words" switch, both on by default. Works in light and dark mode, and respects reduced motion, transparency and contrast settings. For now all three columns use the sample index, so they look the same.
```bash
.venv/bin/streamlit run app/streamlit_app.py
```

**Query parser** (`dhvani/rank/parser.py`)
Turns one query into stricter-to-looser searches: exact phrase, part of the phrase (two neighbouring words), all words, all words with variants, then any word. It stops once it has k results. Articles found at a stricter stage rank above looser ones, and within a stage the chosen ranker decides. Each result's explain dict gets `stage` and `stages_run`, and its word scores are always under `terms`. Feedback tokens from Rocchio (all expansions tagged `prf`) don't take part in the phrase and AND stages; they only count in "any word" and in the score.
```python
from dhvani.rank.parser import parse_and_rank
parse_and_rank(q, idx, k=10, ranker="net", doc_filter=None)   # ranker: net, lnc or bm25
```

**Terminal search and --explain** (`app/cli.py`)
Searches from the terminal. With `--explain` it prints every step: the query object, the query vector (tf, df, idf and weights, or the BM25 idf), the postings each term touched with positions, how many articles became candidates and how the heap picks the top K, and a full score breakdown for each result.
```bash
.venv/bin/python app/cli.py "दिल्ली बारिश" --explain
.venv/bin/python app/cli.py "कोहली शतक" --ranker bm25 --k 3 --explain
```
With `--explain` there's also a step 4b showing how many articles each parser stage found and where it stopped. `--no-parser` turns the parser off and `--no-xling` turns translation off.

**Cross-lingual layer** (`dhvani/rank/xling.py`)
English query words become weighted Hindi terms inside the query vector, so "weather tomorrow" is scored against the same Hindi terms as "कल का मौसम". A word's weight is split across its translations, multi-word entries like "prime minister" are matched as phrases, and English stop words are dropped. The dictionary is `dhvani/rank/data/en_hi_news.tsv`; if the MUSE English-Hindi dictionary is saved at `data/muse/en-hi.txt` it's merged in too.
```python
from dhvani.rank.xling import translate
q = translate(exact_query("delhi rain"))   # adds ("दिल्ली", w, "xling"), ("बारिश", w, "xling") ...
```

**Metrics** (`dhvani/eval/metrics.py`)
P@k, R@k, F1, AP, MAP, DCG, nDCG and the 11-point interpolated PR curve, checked against the lecture's own examples (MAP comes out as 0.53). Also reads and writes TREC run files and judgment files.
```python
from dhvani.eval.metrics import evaluate, read_qrels, read_run
per_query, means = evaluate(rankings, qrels_by_query, k=10)   # means: P@10, R@10, MAP, nDCG@10
```

**Experiment runner** (`dhvani/eval/experiments.py`)
Runs every stemming mode x every ranker x every query, writes TREC run files to `data/eval/runs/`, and prints the full results table (overall and per query form), the stemming comparison, per-query wins and losses against no stemming, and English queries with translation off vs on. Modes that aren't built yet are skipped. `dhvani/eval/sample/` has made-up queries and judgments for the sample index so it runs today.
```bash
.venv/bin/python -m dhvani.eval.experiments
.venv/bin/python -m dhvani.eval.experiments --queries eval/queries.tsv --qrels eval/qrels_news.txt
```

**Stop words, idf and Zipf** (`dhvani/eval/corpus_stats.py`)
df, collection frequency and idf for every term, the most frequent terms (Hindi function words like में, का, की come out at the top with idf near 0), a stop word list taken from the data, Zipf's law with a fitted slope, and a stop word experiment: no idf (lnc.lnc) vs idf (lnc.ltc) vs stop words removed. Plots go to `data/eval/` when matplotlib is installed.
```bash
.venv/bin/python -m dhvani.eval.corpus_stats
```

**Index elimination** (`dhvani/rank/speedups.py`)
Scores fewer articles. Query words with low idf (below 0.3 by default) are skipped, always keeping at least the rarest word. With 3 or more query words, an article has to contain at least 75% of them (3 of 4, as in Lecture 7). If that leaves fewer than k articles it relaxes one word at a time. Returns `(results, stats)`, where stats says how many articles were scored compared with full search. `overlap_at_k()` measures how much of the exact top k was kept.
```python
from dhvani.rank.speedups import search_index_elimination, overlap_at_k
results, stats = search_index_elimination(q, idx, k=10)
```

**Champion lists** (`dhvani/rank/speedups.py`)
`ChampionLists(index, r=50, static_scores=None)` keeps each term's r highest-weight articles; with `static_scores` (g(d)) they're ordered by weight + g(d), as in Lecture 7. `search_champions(q, idx, champions, k)` scores only those articles and falls back to the full postings if there are fewer than k. Returns `(results, stats)` like index elimination.

## Tests
101 tests in `partwise-tests/rishit/`, all passing.
```bash
.venv/bin/python -m pytest partwise-tests/rishit -q
```

## What I need from others
- **Dhrithi:** keep `links` and `city` in the index's `meta` (PageRank and the result rows need them), fill `doc_norm` if possible, add `doc_len` if possible, and the `auto` mode (selective stemming) for the third column. Build the none and light indexes on Riya's 300-article sample, then on the full crawl. Use log10 in `idf()` so the numbers match the slides and this branch.
- **Viraja:** point `KGramIndex` at Dhrithi's `idx.vocab` once her index is built. Agree the split with the cross-lingual layer: her language ID gives `en` weight only to real English words, and names like "delhi" match through both layers. Her Rocchio terms use the `prf` tag, which the app and parser already handle.
- **Riya:** the full crawl for the freeze. Keep article text out of git (only metadata in the repo, full text on Drive) because the repo is public.
- **Everyone:** 8 information needs each (Hindi, Hinglish and English forms) and the merge into `main`.

## Next
Speed-ups (index elimination, champion lists, recent tier), date-aware "kal", duplicate collapsing, PageRank and authority, then learning-to-rank after judging.
