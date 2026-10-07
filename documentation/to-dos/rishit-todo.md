# Rishit's to-do

The whole plan in one place, split into what's done, what's happening now, and what's next. Done items are crossed out. Full details are in `documentation/dhvani-plan.md`.

Last updated: 7 Oct, around 14:35 (teammates' status read from their branches on GitHub)

## Done

### Team
- [x] ~~Picked Track 5 and the project: Hindi + Hinglish news search~~
- [x] ~~Checked robots.txt for the Hindi news sites and picked 5 to crawl~~
- [x] ~~Wrote the project plan and split the work between Riya, Dhrithi, Viraja and Rishit~~
- [x] ~~Wrote down the 5 shared formats (`documentation/formats.md`)~~
- [x] ~~Set up the repo, branches and folder structure~~

### Rishit (committed on `rishit`)
- [x] ~~`dhvani` package and `.gitignore`~~
- [x] ~~Sample index (20 hand-written articles) to build ranking on before the real index exists~~
- [x] ~~lnc.ltc scoring with heap top-K~~
- [x] ~~Net score: cosine + zone weights + proximity + recency~~
- [x] ~~BM25~~
- [x] ~~Filters for source, section, state and date, usable by all three rankers~~
- [x] ~~Sample index keeps article text so results can be displayed~~
- [x] ~~Streamlit app, first version: search box, ranker choice and the no stemming / stemming / auto columns~~
- [x] ~~Streamlit: highlighted words and snippets~~
- [x] ~~Streamlit: match chips, sidebar filters, "why this score" breakdown and "only here" tags~~
- [x] ~~Streamlit redesign in an Apple style: top bar, centred search, segmented control, filters popover, grouped result lists~~
- [x] ~~`app/cli.py --explain`: query vector, postings, candidates, heap and per-word scores~~
- [x] ~~Query parser: exact phrase, part of the phrase, all words, all words with variants, then any word~~
- [x] ~~Parser stage shown on each result in the app, a switch to turn it off, and a parser step in `--explain`~~
- [x] ~~Cross-lingual layer: English words become weighted Hindi terms (news dictionary in the repo, MUSE optional)~~
- [x] ~~Translation switch in the app's Filters popover and `--no-xling` in the CLI~~
- [x] ~~Metrics: P@k, R@k, MAP, nDCG and 11-point PR, checked against the lecture examples~~
- [x] ~~Experiment runner: every stemming mode x every ranker x every query, run files, tables, stemming comparison, translation off vs on~~
- [x] ~~Stop words and idf on the Hindi corpus: top-idf table, stop words from the data, Zipf fit, no idf vs idf vs removed~~
- [x] ~~Feedback (Rocchio `prf`) match type shown in the app, and kept out of the parser's strict stages~~
- [x] ~~Index elimination: skip low-idf query words and only score articles matching most of the query~~
- [x] ~~Champion lists, with the high/low fallback and optional g(d) ordering~~
- [x] ~~Recent-news tiers: newest articles first, older tiers only if needed~~
- [x] ~~`requirements.txt` for the whole team~~
- [x] ~~Date-aware kal: tell yesterday from tomorrow from the query, boost articles about the right day~~
- [x] ~~Date-aware kal shown in the app (switch, tag, boost in Score details) and the CLI (`--explain` step 4c, `--no-kal`)~~
- [x] ~~PageRank and first-to-publish authority in g(d), usable by the net score and champion lists~~
- [x] ~~Authority g(d) used in the app and CLI, with recency, PageRank and first to publish shown in the score breakdown~~
- [x] ~~Duplicate collapsing: one result per wire story with "also in" the other papers, in the app and CLI~~

## In progress

### Rishit: next up
- [ ] Speed-ups in the app and CLI: a speed-up choice, and how many articles were scored
- [ ] Speed-ups results table in the experiment runner: overlap with full search and articles scored
- [ ] My 8 information needs, picked from stories in Riya's crawl
- [ ] Merge `rishit` into `main` again after those three
- [ ] Plug the real pieces in on `main`: Viraja's `build_query` instead of `query_stub`, Dhrithi's index instead of `SampleIndex`, headlines and text from `idx.text`
- [ ] End-to-end check with Viraja: Hindi, Hinglish and English forms of a need all find the right articles (H12)

## Next

### Rishit: required
- [ ] Run every experiment on the frozen corpus: lnc.ltc vs BM25, translation off vs on, stemming modes, speed-ups, wins and losses, and the plots
- [ ] Judging the pooled results with the team
- [ ] Learning-to-rank (after judging)
- [ ] My results tables, report section and video segment
- [ ] Put the final report and video together (H28 to H34)
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
| From | What | Status |
|---|---|---|
| Dhrithi | Real indexes for none, light and auto with the `formats.md` methods | none, light, aggr and auto exist and were tested on Riya's sample; full-crawl build waits for the freeze |
| Dhrithi | `doc_norm` filled, `links` and `city` kept in `meta`, `doc_len` if possible | Done |
| Dhrithi | `analyze(text, mode)` so queries are processed like articles | Done (`text/analyzer.py`) |
| Viraja | Query object with Hinglish expansions | Done (`dhvani/query/build.py`), merged into `main` |
| Viraja | Agree the split with the cross-lingual layer for English words and names | Asked |
| Riya | Article file with `links`, `dup_of`, `date`, `source`, `section`, `state` | 300-article sample done with every field; full crawl not done |
| Riya | Pooling script | Started (`dhvani/eval/pool.py`); CLI not finished |
| Everyone | 8 information needs each, then judgments | Viraja's 8 done; the rest not yet |

### Riya (from branch `riya`)
- [x] ~~robots.txt checker (RFC 9309, wildcards, longest match) with tests against the real sites' files~~
- [x] ~~Mercator frontier: priority front queues, per-site back queues, heap enforcing the 8 s gap~~
- [x] ~~Sitemap parser (Google News and archive sitemaps), URL normalization, route filters, polite backoff~~
- [x] ~~JSON-LD extraction with HTML fallback, IST dates, state and city from URLs, `links`, no author names~~
- [x] ~~Near-duplicate clustering: MD5, 4-word shingles, MinHash + LSH, 24 h window, Jaccard 0.70 (0 duplicates in the 300 sample)~~
- [x] ~~300-article sample (`data/news_sample_300.jsonl`) with corpus and dedup stats~~
- [x] ~~Crawler fix for burst detection (`is_bursting`), merged into `main`~~
- [ ] Full crawl of 5,000+ articles (needed for the freeze)
- [ ] Adaptive recrawl, burst detection, conditional requests
- [ ] Pooling CLI, format-compliance test, dedup threshold precision/recall table

### Dhrithi (from branch `Dhrithi`)
- [x] ~~Normalizer, tokenizer, `analyze(text, mode)` for none, light and aggr~~
- [x] ~~Light stemmer (Ramanathan & Rao) and aggressive stemmer~~
- [x] ~~Positional index with headline and body zones, df, metadata, save and load, JSONL builder~~
- [x] ~~Boolean AND (smallest list first), skip pointers, phrase and proximity search~~
- [x] ~~`idf()` helper and a hand-made stop word list~~
- [x] ~~Selective stemming (the auto column)~~
- [x] ~~Stop word analysis and idf aligned to base 10~~
- [x] ~~Auto stemming works on a fresh checkout without the generated files~~
- [ ] Indexes built on the full crawl
- [ ] Stem-diff report
- [ ] YASS, extended biwords, compression (extras, can wait)

### Viraja (from branch `Viraja`)
- [x] ~~Language ID, Roman spellings, lecture Soundex, Dhvani-code, learned edit distance (trained on 50k Aksharantar pairs)~~
- [x] ~~k-gram candidates, top-5 weighted variants, Viterbi context correction~~
- [x] ~~`build_query` in the shared query format, Rocchio pseudo-relevance feedback (`prf` tag)~~
- [x] ~~Word-level results (Dhvani-code best: Acc@1 0.931 on Aksharantar) and the 50-name test set, edit-cost heatmap~~
- [x] ~~8 information needs (V01 to V08)~~
- [ ] Point the k-gram index at Dhrithi's real vocabulary
- [ ] End-to-end test with Rishit's ranker after the merge

### Everyone
- [ ] 8 information needs each (Hindi, Hinglish and English forms)
- [x] ~~Riya's, Dhrithi's and Viraja's branches merged into `main` (sample corpus left out of git)~~
- [x] ~~`rishit` merged into `main` (up to duplicate collapsing)~~
- [x] ~~Riya's crawler fix and Dhrithi's auto stemming fix merged into `main`~~
- [ ] Judging after the freeze
- [ ] Own results table, report section and video segment

### Open issues
- **Article text in a public repo.** Riya's `data/news_sample_300.jsonl` is left out of git on `main`, but it's still committed on her own branch. Plan: share the full text on Drive.
- ~~**Merge clashes:** `.gitignore` files combined into one on `main`, `dhvani/eval/__init__.py` combined.~~
- ~~**Tests that need local files:** fixed by Dhrithi; auto stemming now falls back to no stemming when the generated files are missing.~~
- **Auto column on a fresh checkout:** without Dhrithi's generated files the auto column gives the same results as no stemming. She needs to commit the small candidates file or document how to generate it.
- **Two test files share a name:** `test_build.py` and `test_scoring.py` are in both `tests/` and `partwise-tests/`, so running both folders in one pytest command errors. Run them separately, or rename Dhrithi's two files.
- ~~**Folder layout:** Dhrithi's top-level `text/` and `index/` import fine on `main`.~~
- ~~**idf log base:** Dhrithi moved to log10, same as this branch and the slides.~~

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
