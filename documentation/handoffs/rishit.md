# Handoff

What I've built, where it lives, and how the rest of the team can use it. Only covers work that's committed on the `rishit` branch.

Last updated: 7 Oct, after adding the translation switch

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
| `43f3c50` first version of the streamlit app with the three stemming columns | `app/streamlit_app.py` |
| `896eab0` highlighted query words and snippets in the app | best-matching sentence for each result, matched words coloured |
| `6d88458` match chips, filters and score breakdown in the app | rest of `app/streamlit_app.py` |
| `4c95b31` redesigned the app in an apple style | new look for `app/streamlit_app.py` |
| `202fac6` search from the terminal with --explain | `app/cli.py` |
| `bdd6b29` query parser that tries the exact phrase first | `dhvani/rank/parser.py` |
| `6063301` parser stages shown in the app and the cli | `app/streamlit_app.py`, `app/cli.py` |
| `8cc6b07` cross-lingual layer for english queries | `dhvani/rank/xling.py` and the English to Hindi news dictionary |
| translation switch in the app and cli | `app/streamlit_app.py`, `app/cli.py` |

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

**The app** (`app/streamlit_app.py`)
Styled after Apple's design guidelines. A translucent bar sits at the top, and a big centred search field has suggestion pills under it. A segmented control picks the ranking model (net score, lnc.ltc or BM25), and a Filters popover next to it holds newspaper, section, state, results per column and date range. Results show in three grouped lists side by side: no stemming, stemming and auto. Each row shows the paper, section, place, date and score, the headline and best-matching sentence with matched words tinted by match type, chips for how each word matched, an "Only here" tag if the result isn't in the other columns, a small label for the parser stage that matched it, and a "Score details" disclosure with the full breakdown. The Filters popover has a "Smart query parsing" switch and a "Translate English words" switch, both on by default. Works in light and dark mode, and respects reduced motion, transparency and contrast settings. For now all three columns use the sample index, so they look the same.
```bash
.venv/bin/streamlit run app/streamlit_app.py
```

**Query parser** (`dhvani/rank/parser.py`)
Turns one query into stricter-to-looser searches: exact phrase, part of the phrase (two neighbouring words), all words, all words with variants, then any word. It stops once it has k results. Articles found at a stricter stage rank above looser ones, and within a stage the chosen ranker decides. Each result's explain dict gets `stage` and `stages_run`, and its word scores are always under `terms`.
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

## Tests
64 tests in `partwise-tests/rishit/`, all passing.
```bash
.venv/bin/python -m pytest partwise-tests/rishit -q
```

## What I need from others
- **Dhrithi:** the real index with the methods in `formats.md`. My code only needs `postings`, `df`, `N`, `vocab`, `doc_norm` and `meta`. If you add `doc_len`, BM25 will use it directly.
- **Viraja:** the query object with expansions. The ranker already reads the expansion weights.
- **Riya:** `links` and `dup_of` in the article file, for PageRank and duplicate collapsing.

## Next
The metrics, the experiment runner, then speed-ups, PageRank and authority.
