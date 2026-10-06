# Viraja handoff — the Hinglish layer (`dhvani/query/`)

Living notes on what my part gives the team, what I need back, and the calls I
made at forks in the road. If you rename something I expose, tell me first.

## What I expose right now (Phase 0–2)

All importable as `from dhvani.query.X import ...`:

| Module | Function | What it does |
|---|---|---|
| `langid` | `script(word)` | `"devanagari"` or `"roman"` |
| `langid` | `classify(word)` | `{"hi","hinglish","en"}` weight dict for one word |
| `roman` | `romanize(word)` | canonical Roman spelling of a Devanagari word, with the final-schwa drop (कमल→kamal) |
| `phonetics` | `soundex(word)` | classic lecture Soundex on a Roman string |
| `phonetics` | `dhvani_code(word)` | our Hindi Soundex; script-agnostic (मौसम / mausam / mosam → `585`) |
| `editdist` | `levenshtein(a,b)` | plain unit-cost edit distance |
| `editdist` | `learn_costs(pairs)` / `distance(a,b,table,default)` | learned edit distance (−log P, 2–3 EM re-aligns on Aksharantar) |
| `editdist` | `load_costs(path)` | loads `dhvani/query/edit_costs.json` (shipped, trained on 50k Aksharantar pairs) |
| `kgram` | `KGramIndex(vocab).candidates(word)` | k-gram candidate terms ranked by Jaccard |
| `match` | `weighted_variants(word, index, costs)` | top-5 `(term, weight, "phonetic")` variants — the production path |
| `build` | `build_query(raw)` | the **query object** (format 4) — exact-match only for now (phonetic expansions wire in during Phase 3) |

Tests: `partwise-tests/viraja/` (**35 passing**). Run `python -m pytest partwise-tests/viraja/`.

### Phase 2 word-level results (Aksharantar test split, 1500 queries / 1156-word vocab)
| matcher | accuracy@1 | MRR |
|---|---|---|
| levenshtein | 0.895 | 0.921 |
| soundex | 0.912 | 0.935 |
| **dhvani (ours)** | **0.931** | **0.947** |
| learned | 0.906 | 0.934 |

Our Dhvani-code tops the table. Learned edit distance's cheapest edits come out as real Hinglish confusions (`q→k`, `z→j`, dropped schwa `a→∅`, `v→w`, `u→o`), rebuild with `python -m dhvani.query.evaluate`.

## For Rishit

- `build_query(raw)` returns exactly the format-4 object your ranker scores. It
  is meant to **replace your temporary `dhvani/rank/query_stub.py`** — swap
  `from dhvani.rank.query_stub import exact_query` for
  `from dhvani.query.build import build_query` whenever you're ready. Same shape,
  so nothing downstream changes.
- For now every token has a single `("<word>", 1.0, "exact")` expansion. The
  phonetic variants already exist (`match.weighted_variants` returns
  `(term, weight, "phonetic")`); in **Phase 3** I append them to each token's
  `expansions` list inside `build_query`. The object shape will not change, so
  your scoring code keeps working as I grow it.

## What I need from the team

- **From Dhrithi — the index vocabulary (`idx.vocab`), by ~H6.** The k-gram
  index (`KGramIndex`) takes any iterable of terms; Phase 2 is built and tested
  against the **Aksharantar word list** as a stand-in, so I'm **not blocked**.
  When her index lands I point `KGramIndex` at `idx.vocab` and re-run
  `test_kgram.py` — no code change beyond the vocab source.
- **From Rishit (Phase 3) — his `dhvani/rank/`** so I can run `build_query`
  output through his ranker end-to-end.
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

6. **Learned edit distance treats a match as free (cost 0), not −log P(x,x).**
   This makes it a proper distance (identical strings → 0); the learned table
   still governs every substitution/insertion/deletion.

7. **`edit_costs.json` is committed** under `dhvani/query/` (4.6 KB, trained on
   50k Aksharantar pairs). It's a small model artifact, not article text, so the
   matcher works out of the box without anyone re-downloading the 33 MB dataset.
   The dataset itself stays under git-ignored `data/`. Regenerate with
   `python -m dhvani.query.aksharantar` then `python -m dhvani.query.editdist`.

8. **Aksharantar loads from `hin.zip` directly, not `load_dataset(..., "hin")`.**
   The old per-language config was removed from the HF dataset; it now ships one
   zip per language, so `aksharantar.py` pulls `hin.zip` via `huggingface_hub`.

## Dependency note for packaging
Runtime + tests need `regex` and `pytest`. Re-training the edit costs needs
`huggingface_hub` (to pull `hin.zip`); the shipped `edit_costs.json` means
teammates don't need it just to run the matcher. Phase-4 heatmap will want
`numpy`/`matplotlib`. We still have no shared `requirements.txt` — someone
should add one and I'll list my deps there.
