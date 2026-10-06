# Rishit's handoff

What I've built, where it lives, and how the rest of the team can use it. Only covers work that's committed on the `rishit` branch.

Last updated: 6 Oct, after "sample index keeps article text for display"

## My part
Ranking, cross-lingual layer and the app. Code lives in `dhvani/rank/` and `app/`, tests in `partwise-tests/rishit/`.

## Committed so far

| Commit | What it does |
|---|---|
| `574e7c8` set up the dhvani package and a sample index to build ranking on | `dhvani` package, `.gitignore`, and `dhvani/rank/sample_index.py` |
| `9a8a1ba` lnc.ltc scoring with heap top-k | `dhvani/rank/vsm.py` and `dhvani/rank/query_stub.py` |
| `23cbb1a` net score with zone weights, proximity and recency | `dhvani/rank/scoring.py` |
| `0009026` added bm25 | `dhvani/rank/bm25.py` |
| `e1958f1` filters for source, section, state and date | `dhvani/rank/filters.py`, plus a `doc_filter` option on all three rankers |
| `728c3e4` sample index keeps article text for display | `SampleIndex.articles` holds headline and body |

## How to use it

**Sample index** (`dhvani/rank/sample_index.py`)
20 hand-written Hindi articles across weather, sports, politics, business, crime, education, entertainment and national news. It has the same methods as the real index in `formats.md`: `postings(term, zone)`, `df(term)`, `N`, `vocab`, `doc_norm`, `meta`. Two articles are the same wire story and a few link to each other, for duplicate and PageRank testing.
```python
from dhvani.rank.sample_index import SampleIndex
idx = SampleIndex.load("none")
```

**Query stub** (`dhvani/rank/query_stub.py`)
Builds the query object from `formats.md` with exact matches only, until Viraja's layer is ready.
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

## Tests
36 tests in `partwise-tests/rishit/`, all passing.
```bash
.venv/bin/python -m pytest partwise-tests/rishit -q
```

## What I need from others
- **Dhrithi:** the real index with the methods in `formats.md`. My code only needs `postings`, `df`, `N`, `vocab`, `doc_norm` and `meta`. If you add `doc_len`, BM25 will use it directly.
- **Viraja:** the query object with expansions. The ranker already reads the expansion weights.
- **Riya:** `links` and `dup_of` in the article file, for PageRank and duplicate collapsing.

## Next
Streamlit app, `--explain` CLI, query parser, speed-ups, cross-lingual layer, then PageRank and authority.
