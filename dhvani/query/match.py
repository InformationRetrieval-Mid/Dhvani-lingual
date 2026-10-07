"""Put the four matchers together: generate candidates, re-rank, pick top-5.

Pipeline for one query word:

    word ─► KGramIndex.candidates ─► ~N candidate terms
                                         │
         ┌───────────────┬──────────────┼───────────────┐
         ▼               ▼              ▼                ▼
    Levenshtein      Soundex       Dhvani-code     Learned edit dist
         └───────────────┴──────────────┴───────────────┘
                                         ▼
                         rank, keep TOP-5, soften to weights

All four matchers are exposed so they can be compared head-to-head (that is the
Phase-5 results table). The **production** path is ``weighted_variants`` which
re-ranks by learned edit distance — the variants it returns are what Phase 3
drops into each query token's ``expansions`` list with source ``"phonetic"``.
"""

import math

from dhvani.query.editdist import distance as learned_distance
from dhvani.query.editdist import levenshtein
from dhvani.query.kgram import _canonical
from dhvani.query.phonetics import dhvani_code, soundex

MATCHERS = ("levenshtein", "soundex", "dhvani", "learned")


def _ranked(word, index, matcher, costs=None, pool=50):
    """Rank k-gram candidates for ``word`` by one matcher.

    Returns ``[(term, score), ...]`` best-first, where a lower score is better
    (distance for ``levenshtein``/``learned``; a 2-level key-match-then-distance
    score for ``soundex``/``dhvani``).
    """
    cands = index.candidates(word, limit=pool)
    # Always include same-Dhvani-code terms, even if their k-gram overlap was too
    # low to make the pool (e.g. iyer / अय्यर). Without this the right phonetic
    # match can be truncated away before any matcher ranks it.
    seen = {term for term, _j in cands}
    for term in index.phonetic_candidates(word):
        if term not in seen:
            cands.append((term, 0.0))
            seen.add(term)
    qr = _canonical(word)

    scored = []
    if matcher == "levenshtein":
        for term, _j in cands:
            scored.append((term, float(levenshtein(qr, _canonical(term)))))
    elif matcher == "learned":
        if costs is None:
            raise ValueError("the 'learned' matcher needs costs=(table, default)")
        table, default = costs
        for term, _j in cands:
            scored.append((term, learned_distance(qr, _canonical(term), table, default)))
    elif matcher in ("soundex", "dhvani"):
        key = soundex if matcher == "soundex" else dhvani_code
        qkey = key(qr)
        for term, _j in cands:
            tr = _canonical(term)
            # Same phonetic key ranks first (0); break ties by Levenshtein.
            same = 0.0 if key(tr) == qkey else 1.0
            scored.append((term, same + levenshtein(qr, tr) / 100.0))
    else:
        raise ValueError(f"unknown matcher {matcher!r}; choose from {MATCHERS}")

    scored.sort(key=lambda item: (item[1], item[0]))
    return scored


def rank(word, index, matcher="learned", costs=None, k=5, pool=50):
    """Top-``k`` ``(term, score)`` candidates for ``word`` under one matcher."""
    return _ranked(word, index, matcher, costs=costs, pool=pool)[:k]


def _softmax_weights(distances, temperature=1.0):
    """Turn distances into weights: softmax of −distance (closer ⇒ larger)."""
    neg = [-d / temperature for d in distances]
    hi = max(neg)
    exp = [math.exp(x - hi) for x in neg]   # shift for numerical stability
    total = sum(exp)
    return [e / total for e in exp]


def weighted_variants(word, index, costs, k=5, pool=50, temperature=1.0, code_bonus=4.0):
    """Production path: top-``k`` variants as query expansions.

    Returns ``[(term, weight, "phonetic"), ...]`` with weights summing to 1.0,
    ready to extend a query token's ``expansions`` list.

    Two things keep the weights meaningful when the query word is itself in the
    index (e.g. "iyer" is an English word in some articles):

    - the **exact self-match is excluded** — it's already the ``"exact"``
      expansion, and leaving it in the softmax would crush every real variant to
      a near-zero weight.
    - candidates that share the query's **Dhvani-code** (true homophones like
      अय्यर / एयर for "iyer") get a distance bonus, so they rank above mere
      spelling near-misses and actually carry weight.
    """
    qr = _canonical(word)
    qcode = dhvani_code(qr)
    variants = []
    for term, dist in _ranked(word, index, "learned", costs=costs, pool=pool):
        if _canonical(term) == qr:
            continue  # the exact self-match is the "exact" expansion already
        same_code = bool(qcode) and dhvani_code(_canonical(term)) == qcode
        variants.append((term, dist - (code_bonus if same_code else 0.0)))

    variants.sort(key=lambda item: (item[1], item[0]))
    top = variants[:k]
    if not top:
        return []
    weights = _softmax_weights([d for _, d in top], temperature=temperature)
    return [(term, round(w, 4), "phonetic") for (term, _d), w in zip(top, weights)]
