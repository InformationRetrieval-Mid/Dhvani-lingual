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

## In progress

### Rishit
- Nothing uncommitted right now. Next up is the query parser.

## Next

### Rishit
- [ ] Query parser: phrase, then AND, then phonetic AND, then free text
- [ ] Speed-ups: index elimination, champion lists, recent-news tier
- [ ] Snippets with matched words coloured by match type
- [ ] Cross-lingual layer: English words into weighted Hindi words (MUSE + our own news dictionary)
- [ ] Date-aware "kal"
- [ ] Collapsing duplicate wire stories ("also in: ...")
- [ ] PageRank and "first to publish" authority in g(d)
- [ ] Learning-to-rank (after judging)
- [ ] Dense re-ranker (only if there's time)

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
