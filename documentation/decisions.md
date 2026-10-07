# Decisions

A running list of the choices we made and why. Newest at the bottom.

## Project

**Track 5, Hindi only to start.** Track 5 fits our team best and lets the tokenizing, stemming, Soundex and spelling-correction lectures do the real work instead of just being a label. We started with Hindi only so we finish something solid in 36 hours. More languages can come later as the roadmap.

**Hindi news as the corpus.** The brief literally suggests a regional news search engine with precision and recall with and without stemming. News also gives us dates, sections and wire-story duplicates, which our ranking can use.

**Crawl only sites that allow it.** We checked robots.txt for every site. BBC Hindi says no crawling and no datasets in its robots.txt, and News18 and NDTV blocked us, so we left all three out. We use an honest bot name and wait 8 seconds between requests to the same site.

**Article text stays local.** News articles are copyrighted, so only code and URLs go on GitHub.

**Stemming shown side by side.** Every search shows no stemming, stemming and auto next to each other. The brief asks for results with and without stemming, and seeing it per query is more convincing than one table.

**English news idea kept small.** Riya suggested crawling English news too. A full English search engine would mean a second analyzer and index, merging scores across languages and translating articles, which is too much for 36 hours. If there's time after H12, we'll use English coverage only as a small "also reported in English" authority signal.

## Team and workflow

**Work split by component.** Riya does the crawler, Dhrithi does text processing and indexes, Viraja does the Hinglish layer, Rishit does ranking and the app. Each person owns one Track 5 requirement, one original idea and one results table, because individual contribution is graded.

**Everyone at 27 hours.** We kept the split even so nobody carries more than the others.

**Shared formats agreed up front.** The article file, analyzer, index, query object and run file are written down in `formats.md` so we can all build at the same time without waiting on each other.

**Own branches, merge at checkpoints.** Everyone commits to their own branch and merges into `main` only at the checkpoints, so `main` always works.

**Sample corpus stays out of git on main.** When merging Riya's branch, `data/news_sample_300.jsonl` was left out because the repo is public and it holds full article text. Her stats reports, which only have counts, are kept.

**One combined .gitignore.** Each branch had its own. On `main` they're merged into one: everything in `data/` is ignored except the placeholder and Riya's stats reports, and built indexes are ignored too.

**Commits as ourselves.** Every commit is under the person who did the work. AI help is declared in the report's AI-use section instead.

## Rishit's ranking code

**A sample index to start with.** Dhrithi's real index won't be ready for a few hours, so I made a small index over 20 hand-written Hindi articles. It has exactly the same methods as the real one, so swapping it out later needs no other changes. I called it a sample index rather than a fake one.

**lnc.ltc as the main scorer.** It's the standard SMART scheme from the lectures. I used 1 + log10(tf) for the tf weight because the lecture 7 slides correct the log(1 + tf) version.

**Heap for the top results.** Picking the top K with a heap is cheaper than sorting every score, as lecture 7 points out.

**Query stub with exact matches.** Viraja's query layer isn't ready yet, so a small stub builds the same query object with exact matches only. The ranker already uses expansion weights, so phonetic and translated variants will plug straight in.

**Net score on top of cosine.** Headline matches count more than body matches, query words close together get a bonus, and newer articles get a boost. Each part is shown separately so we can explain every score in the demo.

**"Now" is the newest article.** Recency is measured from the newest article in the index instead of the real clock, so results don't change depending on when we run them.

**BM25 alongside lnc.ltc.** BM25 is outside the syllabus, so it earns extra marks, and it gives us a strong baseline to compare against. I used the version of idf that never goes negative, so common Hindi words like का don't get penalised.

**Filters applied before picking the top results.** Source, section, state and date filters run before the top K is chosen, so a filtered search still gets its best matches instead of a few leftovers.

**Streamlit for the app.** The frontend isn't graded, and Streamlit gives us three columns, filters and a score breakdown with very little code.

**Matches coloured by type.** Exact, phonetic and translated matches get different colours, so the demo shows where each result came from at a glance.

**Snippets show the best sentence.** Each result shows the first sentence that contains a query word, falling back to the opening words. It's quick, and it shows the reader why the article matched.

**"Only here" tags.** When a result shows up in just one of the three stemming columns, it gets tagged. That makes the effect of stemming easy to spot in the demo without reading every column.

**Score breakdown in the app.** Every result has a dropdown showing how its score was built. The brief asks us to show weights and scores, not just final results, and this does it live.

**Rebase instead of merge for my own branch.** When GitHub had a small edit I'd made on the website, I put my local commits on top of it instead of making a merge commit. The history stays a straight line and is easier to read.

**Apple-style redesign.** The frontend isn't graded, but the demo video is, and a clean interface makes the system easier to follow on screen. We followed Apple's design guidelines: system font with tight tracking on large text, a translucent top bar, one accent colour, a segmented control for the ranking model, and filters tucked into a popover so the main page stays simple. Results are grouped lists like the iPhone Settings app.

**Styling lives inside the app file.** We kept all the styling in `app/streamlit_app.py` instead of adding a Streamlit theme file, so the look is in one place. The catch is that Streamlit's own controls default to red, so a few of them get a small colour shift to blue in CSS.

**An explain mode in the terminal.** The brief wants the video to show postings, weights and scores, not only the final results. `--explain` prints each stage in order so we can walk through one query live. It's in the terminal rather than the app because a plain text dump is easier to read on a screen recording.

**Query parser with a cascade.** Lecture 7 shows one free-text query being run as a phrase first, then as shorter phrases, then as a plain vector space query. We do the same with five stages and stop once we have enough results. An exact phrase match is a much stronger signal than scattered words, so it always ranks above them, and the ranker only decides the order within a stage.

**Phrases stay inside one zone.** A phrase only counts if the words are next to each other within the headline or within the body. Otherwise the last word of a headline and the first word of the body would wrongly count as a phrase.

**AND starts from the rarest word.** Intersecting the shortest postings list first keeps the result small from the start, which is the query optimisation from Lecture 1.

**Cross-lingual layer as dictionary-based query translation.** English words are looked up in an English to Hindi dictionary and their translations go into the same query vector as Hindi words. That keeps cross-lingual search inside the vector space model, which is what Track 5 asks for, instead of translating whole queries with a separate system.

**Weight split across translations.** "rain" becomes बारिश 0.7 and वर्षा 0.3, so a word with several translations doesn't count more than a word with one.

**Phrases first.** "prime minister" and "stock market" mean something different from their single words, so the longest dictionary phrase is matched first.

**Our own news dictionary, MUSE optional.** A small dictionary of common news words lives in the repo so translation works without any download. The bigger MUSE dictionary is merged in automatically if someone downloads it, and our entries win where both have a word.

**Only top-level data/ is ignored.** The old `.gitignore` rule ignored every folder called data, which would have kept the dictionary out of git. It now only ignores the top-level `data/` folder where crawled articles and downloads live.

**Metrics checked against the lecture.** The tests use the lecture's own worked examples: AP of 0.62 and 0.44 giving MAP 0.53, P@5 of 0.6 and R@5 of 0.5. If those numbers match, we can trust the tables built on top of them.

**Judgments per information need.** Each need is written several ways (Hindi, Hinglish, English) and judged once. Every form is scored against the same judged articles, so we can compare how well each form does on equal terms.

**The runner skips what isn't built yet.** Stemming modes that don't exist yet are skipped with a note instead of crashing, so the runner works from day one and fills in as the indexes arrive.

**Stop words come from the data.** Instead of typing in a Hindi stop word list, we rank terms by document frequency. The words with the lowest idf (में, का, की, के) are the stop words, which shows what idf is doing.

**Three ways to handle stop words.** No idf (lnc.lnc) lets every word count fully, idf (lnc.ltc) keeps stop words but pushes them towards zero, and removing them drops them from the query. Comparing the three shows whether removing stop words still matters once idf is in place.

**Feedback words only count in scoring.** Viraja's Rocchio expansion adds words from the top results as extra query tokens tagged `prf`. They aren't words the user typed, so the query parser leaves them out of the phrase and "all words" stages; otherwise a good result could be dropped just for missing a feedback word. They still add to the score and to the "some words" stage, and the app shows them as purple "Feedback" matches.

**Wait for Dhrithi before covering doc_norm.** Dhrithi's index leaves `doc_norm` empty, which lnc.ltc needs. The ranker can work it out from her postings itself, and that change is written, but we're holding it back to give her time to fill it in her own index first. If she doesn't, we commit the fallback. She filled `doc_norm` (same lnc formula), `doc_len`, `links` and `city` in her index, so the fallback was dropped.

**idf uses log10 everywhere.** The lecture slides use log10(N/df), and so does this branch. The base doesn't change any ranking, but the idf numbers in the report should all be on the same scale, so we've asked Dhrithi to switch her `idf()` from the natural log as well.

**Index elimination relaxes instead of returning nothing.** Skipping common words and asking for most of the query words cuts how many articles get scored, which is the point. But on a short or unusual query that rule can leave too few articles, so it loosens one word at a time until there are k. Speed shouldn't cost the user an empty page.

**Champion lists fall back instead of coming up short.** r is fixed when the lists are built, so a query can end up with fewer than k contenders. Instead of returning a short page, the search then scores the full postings, which is Lecture 7's high list then low list. Ordering by weight + g(d) is built in so recency and PageRank can shape the lists later.

**Fresh news first, even over a slightly better older match.** The tiered search stops at the newest tier once it has k results, so an older article with a higher cosine can be left out. For news that's usually what a reader wants, and it means only a fraction of the articles get scored. Searching all tiers gives back the exact ranking when freshness doesn't matter.

**One requirements.txt for everyone.** It lists what every part of the code actually imports, so anyone can set up with one command. Plotting and dataset downloads are marked optional because the search engine runs without them.

**kal defaults to yesterday.** When a query has कल but no other clue, we treat it as yesterday, because news mostly reports what already happened.

**Weather words mean tomorrow.** "kal ka mausam" is almost always about tomorrow's weather, and weather news is mostly forecasts, so weather words count as a future cue.

**The kal boost multiplies the score instead of adding to it.** A flat bonus let an unrelated article jump to the top just because it was published on the right day. Multiplying keeps the boost proportional to how relevant the article already is.

**kal only reorders within a parser stage.** The query parser puts exact-phrase matches above looser ones on purpose. The kal boost respects that and only changes the order inside a stage, so a date boost can never push a stricter match below a looser one.

**Dangling articles spread their vote evenly.** Many news articles don't link to anything else we crawled. In PageRank their score is shared equally across all articles, so it isn't lost and the scores still add up to 1.

**Recency still leads in g(d).** The static score is 0.5 recency, 0.3 PageRank and 0.2 first to publish. For news, how fresh a story is matters most, and the link graph between crawled articles is sparse, so PageRank and the original flag adjust the order rather than dominate it.

**The original gets the credit, not the newest copy.** When several papers run the same wire story, recency alone favoured the latest copy. First-to-publish credit gives the boost to the article the others copied, so the original ranks first.

**Authority is on by default in the app and CLI.** The net score now uses the full g(d) (recency, PageRank and first to publish) unless it's switched off, so the original of a wire story ranks above its copies. The switch and `--no-authority` are there to show the difference side by side.

**Duplicates collapse to the best-ranked copy, not always the original.** Authority already pushes the original up, so usually it's the one kept. If a copy ranks higher for a query, that copy is shown and the original is listed under "also in", so the user sees the best match first.

**Ask for 3k results before collapsing.** Collapsing can remove results, so the ranker returns three times as many and the list is cut to k afterwards. That way the top k still has k different stories.

**Extra explain info stays out of the term scores.** lnc.ltc and BM25 return a plain dictionary of term scores. When kal or collapsing add their own info, the term scores move under "terms" so the app doesn't mistake "also in" for a query word.
