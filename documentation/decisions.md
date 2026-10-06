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
