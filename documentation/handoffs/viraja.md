# Viraja handoff — the Hinglish layer (`dhvani/query/`)

Living notes on what my part gives the team, what I need back, and the calls I
made at forks in the road. If you rename something I expose, tell me first.

## What I expose right now (Phase 0–1)

All importable as `from dhvani.query.X import ...`:

| Module | Function | What it does |
|---|---|---|
| `langid` | `script(word)` | `"devanagari"` or `"roman"` |
| `langid` | `classify(word)` | `{"hi","hinglish","en"}` weight dict for one word |
| `roman` | `romanize(word)` | canonical Roman spelling of a Devanagari word, with the final-schwa drop (कमल→kamal) |
| `phonetics` | `soundex(word)` | classic lecture Soundex on a Roman string |
| `phonetics` | `dhvani_code(word)` | our Hindi Soundex; script-agnostic (मौसम / mausam / mosam → `585`) |
| `build` | `build_query(raw)` | the **query object** (format 4) — exact-match only for now |

Tests: `partwise-tests/viraja/` (24 passing). Run `pytest partwise-tests/viraja/`.

## For Rishit

- `build_query(raw)` returns exactly the format-4 object your ranker scores. It
  is meant to **replace your temporary `dhvani/rank/query_stub.py`** — swap
  `from dhvani.rank.query_stub import exact_query` for
  `from dhvani.query.build import build_query` whenever you're ready. Same shape,
  so nothing downstream changes.
- For now every token has a single `("<word>", 1.0, "exact")` expansion. Phonetic
  and cross-lingual expansions arrive later as **extra entries in the same
  `expansions` list** — the object shape will not change, so your scoring code
  keeps working as I grow it.

## What I need from the team

- **From Dhrithi — the index vocabulary (`idx.vocab`), by ~H6.** I need it to
  build the k-gram candidate index (Phase 2). Until it lands I develop against
  Aksharantar only, so I'm **not blocked** for Phase 1.
- **From the group — Rishit's Phase-0 `dhvani/` package should land on `main`.**
  See decision 1 below.

## Decisions I made at forks

1. **`dhvani/__init__.py` on my branch, identical to Rishit's.**
   Phase 0's "everyone can `import dhvani`" skeleton currently lives only on the
   `rishit` branch, not on `main`. Rather than block, I added a
   `dhvani/__init__.py` that is byte-for-byte Rishit's one-liner, plus
   `dhvani/query/__init__.py`. Because the shared file is identical, merging the
   branches causes **no conflict**. Ideal path: Rishit's Phase-0 setup is merged
   to `main`, then I `git pull` and my `__init__.py` is already in step.

2. **My own query tokenizer (`dhvani/query/tokenize.py`) as a stand-in.**
   Dhrithi's analyzer (format 2) isn't importable yet, and I need to tokenize
   *queries* regardless. I use the same agreed pattern `[\p{L}\p{M}\p{Nd}]+`
   (the `regex` module). Documents are still tokenized only by Dhrithi's
   analyzer — never by this.

3. **Romanization uses a fixed "aa/ii/uu" long-vowel scheme** (आ→aa, ई→ii, ऊ→uu;
   aspirates add "h"). So बारिश→`baarish`, का→`kaa`. This is a *canonical*
   spelling, not how a human would type it — the phonetic layer (Soundex /
   Dhvani-code / learned edit distance) bridges `kaa`↔`ka`. I only do the
   **final** schwa drop the plan asks for; medial schwa deletion is out of scope.

4. **Language ID is a small lexicon-based classifier, not trained.** Ambiguous
   words (main/to/hi/is/me/us/do/he/the/or) carry both readings at 0.5/0.5; the
   word lists are seeds in `langid.py`, easy to grow.

5. **Dhvani-code keeps the full consonant skeleton** (no 3-digit truncation like
   classic Soundex) and collapses adjacent duplicates. Variable length is more
   discriminative for a matching key; the digit labels are chosen so म=5, स=8 to
   hit the plan's `585`.

## Dependency note for packaging
My code needs `regex` (and `pytest` for tests); the edit-distance / heatmap work
later will want `numpy`. We still have no shared `requirements.txt` — someone
should add one in Phase 0 and I'll list my deps there.
