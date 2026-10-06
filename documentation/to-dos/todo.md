# To-do

The whole plan in one place, split into what's done, what's happening now, and what's next. Full details are in `documentation/dhvani-plan.md`.

Last updated: 7 Oct

## Done

### Team
- [x] Picked Track 5 and the project: Hindi + Hinglish news search
- [x] Checked robots.txt for the Hindi news sites and picked 5 to crawl
- [x] Wrote the project plan and split the work between Riya, Dhrithi, Viraja and Rishit
- [x] Wrote down the 5 shared formats (`documentation/formats.md`)
- [x] Set up the repo, branches and folder structure

### Rishit (committed on `rishit`)
- [x] `dhvani` package and `.gitignore`
- [x] Sample index (20 hand-written articles) to build ranking on before the real index exists
- [x] lnc.ltc scoring with heap top-K
- [x] Net score: cosine + zone weights + proximity + recency
- [x] BM25
- [x] Filters for source, section, state and date, usable by all three rankers
- [x] Sample index keeps article text so results can be displayed
- [x] Streamlit app, first version: search box, ranker choice and the no stemming / stemming / auto columns
- [x] Streamlit: highlighted words and snippets
- [x] Streamlit: match chips, sidebar filters, "why this score" breakdown and "only here" tags
- [x] Streamlit redesign in an Apple style: top bar, centred search, segmented control, filters popover, grouped result lists
- [x] `app/cli.py --explain`: query vector, postings, candidates, heap and per-word scores
- [x] Query parser: exact phrase, part of the phrase, all words, all words with variants, then any word
- [x] Parser stage shown on each result in the app, a switch to turn it off, and a parser step in `--explain`

- [x] Cross-lingual layer: English words become weighted Hindi terms (news dictionary in the repo, MUSE optional)
## In progress

### Rishit
- Next up: a translation switch in the app and the CLI.

## Next

### Rishit: required
- [ ] Speed-ups: index elimination, champion lists, recent-news tier
- [ ] Date-aware "kal"
- [ ] Collapsing duplicate wire stories ("also in: ...")
- [ ] PageRank and "first to publish" authority in g(d)
- [ ] Learning-to-rank (after judging)
- [ ] Dense re-ranker (only if there's time)

### Rishit: extras (in rough order)
- [ ] Rank fusion (RRF) of lnc.ltc, BM25 and dense
- [ ] Facet counts next to each filter option, e.g. "Jagran (12)"
- [ ] Query difficulty prediction with a "low confidence" hint
- [ ] Evaluation dashboard tab in the app: P@10, MAP, nDCG and PR curves per ranker and stemming mode
- [ ] Cluster pruning (leaders and followers), compared with champion lists for speed vs quality
- [ ] High/low lists and impact-ordered postings with early stopping
- [ ] Result diversification (MMR) so the top 10 isn't one story repeated
- [ ] Autocomplete with prefix search over the term dictionary

### Rishit: needed from teammates
| From | What | By | Until then |
|---|---|---|---|
| Dhrithi | Real indexes for none, light and auto with the `formats.md` methods, ideally plus `doc_len` and article text | H8 | Sample index |
| Dhrithi | `analyze(text, mode)` so queries are processed like articles | H8 | Sample tokenizer |
| Dhrithi | Metrics code (P@k, MAP, nDCG) | H22 | Nothing needed yet |
| Viraja | Query object with Hinglish expansions | H12 | Exact-match stub |
| Viraja | Agree the handoff: her language ID tags English words, my layer adds translated expansions | Now | Nothing |
| Riya | `news.jsonl` with `links`, `dup_of`, `date`, `source`, `section`, `state` | H8 sample, H18 frozen | Sample articles |
| Riya | Pooling script | H22 | Nothing needed yet |
| Everyone | 8 information needs each, then judgments | H10, H25 | Nothing needed yet |

### Riya
- [ ] robots.txt checker, Mercator frontier, sitemap crawling
- [ ] Article extraction, near-duplicates, MinHash + LSH, adaptive recrawl
- [ ] Pooling script

### Dhrithi
- [ ] Normalizer, tokenizer, stop words and idf study
- [ ] Light, aggressive and YASS stemmers, selective stemming (auto)
- [ ] Positional indexes, Boolean search, extended-biword phrase index, compression
- [ ] Metrics code

### Viraja
- [ ] Language ID, Roman spellings, Soundex, Dhvani-code, learned edit distance
- [ ] k-gram candidates, weighted expansion, context correction
- [ ] Rocchio query expansion

### Everyone
- [ ] 8 information needs each by H10
- [ ] Judging (H22 to H25)
- [ ] Own results table, report section and video segment
- [ ] Merge into `main` at the checkpoints: H3, H8, H12, H22, H28

## Checkpoints
| Hour | What should work |
|---|---|
| H3 | Sample articles and query stub shared, crawler running |
| H8 | A Hindi query shows no-stem and stem results in the app |
| H12 | Hindi, Hinglish and English versions of a query all work |
| H18 | News snapshot frozen |
| H22 | Every system can produce results for all 120 queries |
| H28 | All tables and graphs done |
| H36 | Report, video and repo submitted |
