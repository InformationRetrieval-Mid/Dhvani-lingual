# P2 Handoff - Text Processing & Indexes

**Project:** Dhvani  
**Repository:** `Dhvani-lingual`  
**Branch:** `Dhrithi`  
**Owner:** Dhrithi  
**Current milestone:** Phase 2 complete  
**Test status:** 83 passed, 0 failed

---

## 1. Responsibility

P2 owns the text-processing and indexing layer of Dhvani.

The P2 pipeline currently covers:

- Hindi Unicode normalization
- Hindi/Hinglish tokenization
- No-stemming analysis
- Light stemming
- Aggressive stemming foundation
- Positional indexing
- Headline/body zones
- Document metadata
- Boolean AND search
- Smallest-postings-list-first optimization
- Skip pointers
- Phrase search
- Proximity search
- JSONL corpus ingestion
- Index serialization/loading
- Query-to-index integration

The planned later P2 work includes:

- Corpus-derived stop words
- IDF
- Zipf analysis
- Stem-difference analysis
- Selective/automatic stemming
- YASS
- Extended-biword indexing
- Index compression
- Evaluation tooling

---

# 2. Current architecture

The current flow is:

    Raw article
        |
        v
    normalize()
        |
        v
    tokenize()
        |
        v
    analyze(mode)
        |
        +---- none
        |
        +---- light
        |
        +---- aggr
        |
        v
    Positional Index
        |
        v
    Search
        |
        v
    Query results


For queries:

    raw query
        |
        v
    analyze(query, mode)
        |
        v
    query terms
        |
        v
    Boolean / phrase / proximity search
        |
        v
    matching document IDs

---

# 3. Implemented files

## Text processing

### `text/normalize.py`

Responsible for Unicode normalization.

Current behavior:

- NFC normalization
- Removes zero-width joiner
- Removes zero-width non-joiner
- Handles the specified `हिंदी -> हिन्दी` normalization case
- Collapses repeated whitespace

The normalizer intentionally avoids broad anusvara replacement because generic conversion was found to corrupt valid Hindi words.

---

### `text/tokenize.py`

Uses the `regex` package and the Unicode-aware pattern:

    [\p{L}\p{M}\p{Nd}]+

This keeps:

- Devanagari letters
- Combining marks
- Unicode digits

while treating punctuation and whitespace as token boundaries.

---

### `text/stem.py`

Implements the light Hindi stemmer.

The implementation follows the suffix-stripping behavior used for the project's light stemming requirement.

Examples covered by tests include:

    लड़कियाँ -> लड़क
    लड़कियों -> लड़क
    किताबों -> किताब
    खाना -> खा
    खाता -> खा
    खाती -> खा

---

### `text/aggressive_stem.py`

Provides the current aggressive suffix-based stemmer.

Entry point:

    stem_aggressive(word)

It uses a larger suffix inventory than the light stemmer and is intended to improve recall by collapsing more morphological variants.

Examples:

    लड़कियाँ -> लड़क
    लड़कियों -> लड़क
    किताबों -> किताब
    लड़कों -> लड़क
    लड़के -> लड़क

The aggressive stemmer is currently a suffix-stripping implementation. It is not yet the YASS stemmer.

---

### `text/analyzer.py`

Shared analyzer API:

    analyze(text, mode)

Supported modes:

    none
    light
    aggr

Returns:

    [(term, position), ...]

Example:

    analyze("लड़कियाँ किताबों", "light")

returns:

    [
        ("लड़क", 0),
        ("किताब", 1)
    ]

The analyzer validates unsupported modes.

---

# 4. Index implementation

## `index/positional.py`

Main index class:

    Index(mode)

Supported modes:

    none
    light
    aggr

The index stores:

- document metadata
- vocabulary
- number of documents
- positional postings
- document norms placeholder
- headline/body zones

---

## Index contract

The index exposes:

    idx.postings(term, zone)

where:

    zone = "headline" | "body"

Postings have the form:

    [
        (doc_id, tf, [positions]),
        ...
    ]

The index also exposes:

    idx.df(term)
    idx.N
    idx.vocab
    idx.doc_norm
    idx.meta

Metadata contains:

    source
    date
    state
    section
    dup_of

---

# 5. Search implementation

## `index/search.py`

Implemented:

### Boolean AND

    and_search(idx, terms, zone="body")

Only documents containing every query term are returned.

---

### Smallest-postings-first

The search implementation prioritizes the smallest postings list.

This reduces the candidate document set early and avoids unnecessary intersections.

---

### Skip pointers

Skip pointers are generated for postings lists to accelerate intersections.

Relevant functionality:

    build_skip_pointers()
    intersect_postings()

---

### Phrase search

    phrase_search(idx, terms, zone="body")

Uses positional information to identify terms occurring consecutively.

---

### Proximity search

    proximity_search(
        idx,
        terms,
        distance,
        zone="body"
    )

Finds documents where query terms occur within the requested positional distance.

The current implementation treats the first query term as the anchor and checks whether the other terms occur within the supplied absolute distance.

---

# 6. Query integration

## `index/query.py`

Provides:

    search_query(idx, query, mode=None, zone="body")

The function:

1. Validates the analysis mode.
2. Ensures the query mode matches the index mode.
3. Analyzes the raw query.
4. Extracts analyzed terms.
5. Runs Boolean AND search.

Example:

    search_query(
        light_index,
        "दिल्ली बारिश",
        mode="light"
    )

---

## Comparing no-stem and light

The helper:

    search_both(
        idx_none,
        idx_light,
        query
    )

returns:

    {
        "none": [...],
        "light": [...]
    }

This is the current basis for comparing the two Phase 2 search columns.

---

# 7. JSONL index building

## `index/build.py`

The index builder reads:

    data/news.jsonl

Required article fields:

    doc_id
    headline
    body

Metadata copied into the index:

    source
    date
    state
    section
    dup_of

Supported build modes:

    none
    light
    aggr

Build all three:

    python -m index.build --mode both

Build one:

    python -m index.build --mode none
    python -m index.build --mode light
    python -m index.build --mode aggr

The default input path is:

    data/news.jsonl

---

# 8. Data contract

The article format follows:

    documentation/formats.md

Expected structure:

    {
      "doc_id": "...",
      "url": "...",
      "source": "...",
      "section": "...",
      "state": "...",
      "city": "...",
      "date": "...",
      "headline": "...",
      "body": "...",
      "keywords": [],
      "agency_flag": false,
      "content_hash": "...",
      "dup_of": null,
      "links": []
    }

The builder currently only requires:

    doc_id
    headline
    body

and preserves the relevant metadata fields required by the index contract.

---

# 9. Tests

Current test status:

    83 passed
    0 failed

Tests cover:

- normalization
- tokenization
- light stemming
- aggressive stemming
- analyzer modes
- invalid analyzer modes
- index construction
- postings
- document frequency
- Boolean search
- skip pointers
- phrase search
- proximity search
- JSONL parsing
- malformed JSON
- missing fields
- metadata
- index building
- aggressive index building
- query integration
- none/light comparison

Run the complete suite with:

    C:\Python314\python.exe -m pytest -q

---

# 10. Current limitations

The following are NOT complete yet:

1. Selective/automatic stemming
2. YASS
3. Corpus-derived stop words
4. IDF pipeline
5. Zipf analysis/plotting
6. Stem-diff evaluation
7. Extended-biword index
8. Variable-byte compression
9. Gamma coding
10. Full corpus index
11. Retrieval evaluation
12. Integration into the final Streamlit UI

The aggressive stemmer should not be described as YASS.

---

# 11. Phase 2 completion

Phase 2 is complete.

Implemented Phase 2 requirements:

- positional indexes
- headline/body zones
- metadata
- Boolean search
- smallest-postings-list-first
- skip pointers
- phrase search
- proximity search
- index builder
- query integration
- no-stem/light comparison

Final test state:

    83 passed, 0 failed

---

# 12. Next phase

The next major P2 work is Phase 3:

1. Aggressive stemming refinement
2. Stop-word discovery
3. IDF
4. Zipf analysis
5. Stem-difference tooling
6. Evaluation preparation

After that:

- selective stemming / auto mode
- YASS
- extended-biword indexing
- compression
- final evaluation

---

# 13. Handoff instructions

Before modifying the branch:

    git pull origin Dhrithi

Run tests:

    C:\Python314\python.exe -m pytest -q

Expected current result:

    83 passed

Do not modify the shared analyzer/index contracts without coordinating with the other team members.

In particular, preserve:

    analyze(text, mode)

and:

    idx.postings(term, zone)
    idx.df(term)
    idx.N
    idx.vocab
    idx.doc_norm
    idx.meta

These are shared interfaces.

---

# 14. Important design decision

The index is positional and zone-aware.

Do not replace the positional postings structure with a simple set of document IDs.

The positions are required for:

- phrase search
- proximity search
- future extended-biword functionality

and the headline/body separation is required for zone-aware ranking later.


## P2 Status Update — Phase 2 Complete

### Completed

P2's Phase 1 and Phase 2 text-processing and indexing work has been implemented and tested.

#### Text processing

- Hindi Unicode normalization using NFC.
- Removal of zero-width joiners/non-joiners.
- Hindi `हिंदी` / `हिन्दी` normalization.
- Whitespace normalization.
- Unicode-aware Hindi/Hinglish tokenization using:
  `[\p{L}\p{M}\p{Nd}]+`
- Light Hindi stemming based on the Ramanathan & Rao suffix inventory.
- Aggressive Hindi stemming implemented as a separate analysis mode.

#### Positional indexes

Implemented separate positional indexes for:

- `none`
- `light`
- `aggr`

Each index stores:

- document ID
- term frequency
- positional information
- headline/body zones
- document metadata
- vocabulary
- document frequency

The index follows the shared `Index.load(mode)` / `idx.postings(term, zone)` API.

#### Boolean and positional search

Implemented:

- Boolean AND search
- smallest-postings-list-first processing
- skip pointers
- exact phrase search using positional intersections
- proximity search using positional information

Search has been tested on both synthetic test documents and a real Hindi news corpus.

### Real-corpus validation

A 1,000-article Hindi corpus from ILSUM-2.0 was converted to the shared Dhvani JSONL article format and used to build all three indexes.

Index statistics:

| Index | Documents | Vocabulary |
|---|---:|---:|
| none | 1,000 | 27,263 |
| light | 1,000 | 21,104 |
| aggr | 1,000 | 22,086 |

Real-corpus query testing showed that stemming changes retrieval for some queries while leaving others unchanged.

Examples:

- `उत्तर प्रदेश`: none = 7 results, light/aggr = 9 results
- `तेज बारिश`: none = 5 results, light/aggr = 7 results
- `बारिश`: all modes = 110 results
- `मौसम`: none = 92 results, light/aggr = 93 results

Phrase and positional search were also tested on the 1,000-document corpus.

Example exact phrase results:

- `भारी बारिश` → 46 documents
- `उत्तर प्रदेश` → 41 documents
- `जम्मू कश्मीर` → 27 documents
- `तेज बारिश` → 20 documents

Example proximity searches:

- `बारिश + मौसम`, distance ≤ 3 → 25 documents
- `बारिश + संभावना`, distance ≤ 5 → 15 documents
- `उत्तर + प्रदेश`, distance ≤ 5 → 41 documents

The positional postings were manually inspected on real documents to verify that adjacent terms have consecutive positions.

### Phase 2 status

**P2 backend/core Phase 2 is complete.**

Implemented components:

- positional inverted indexes
- headline/body zones
- metadata storage
- Boolean search
- smallest-postings-list-first optimization
- skip pointers
- phrase search
- proximity search
- query integration
- real-corpus validation

The Streamlit/application integration is not part of P2's implementation and will be handled by the application owner (P4).

### Current limitations / known gaps

The following shared-contract items are still to be completed or extended in later phases:

- `doc_norm` is currently initialized but not populated with TF-IDF document norms.
- Full field indexing beyond headline/body is not yet implemented.
- The full shared query-object format is not yet implemented.
- `yass` and `auto` analysis modes are planned for later phases.
- Stop-word/IDF processing is not yet implemented.
- Selective stemming is not yet implemented.
- The current search layer is Boolean/positional and does not yet provide final ranked TF-IDF/BM25 results.

### Files added for real-corpus validation

- `scripts/make_dev_corpus.py`
- `scripts/test_real_queries.py`
- `scripts/test_real_phrase_search.py`

The development corpus and generated `.pkl` indexes are local test artifacts and should not be committed to Git.

### Git checkpoint

Real-corpus helper scripts were committed and pushed on branch `Dhrithi`:

`7cacc00 — add real corpus testing scripts`

Next P2 work: **Phase 3 — aggressive stemming evaluation, stop words, IDF/Zipf analysis, and stem-diff tooling.**