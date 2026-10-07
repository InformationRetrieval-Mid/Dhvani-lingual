"""Weighted query expansion: add phonetic variants to each query token.

Phase 1–2 gave us the pieces (k-gram candidates re-ranked by learned edit
distance); this is where they meet the query object. For each token we ask
``match.weighted_variants`` for the top-k spelling/phonetic variants and append
them to that token's ``expansions`` list as ``(term, weight, "phonetic")``. The
exact surface form stays as ``(surface, 1.0, "exact")``, so the ranker sees the
literal query *plus* its variants — e.g. ``mosam`` also pulls up ``मौसम``.

Cross-lingual (``"xling"``) expansions are Rishit's; we leave room for them and
never overwrite entries another source already added.
"""

from dhvani.query import match as M


def expand_token(token, index, costs, k=5, en_cutoff=0.6):
    """Append up to ``k`` phonetic variants to one token's ``expansions`` list.

    Skips words that are confidently English (``lang["en"] >= en_cutoff``): a word
    like "farmers" or "earthquake" has no real Hindi homophone, so expanding it
    only injects junk (farmers -> हामॉन्स). English words are the cross-lingual
    layer's job, not the phonetic layer's. Variants already present (the exact
    surface, or one added earlier) are skipped so weights never double up.
    """
    if token["lang"].get("en", 0.0) >= en_cutoff:
        return token
    seen = {term for term, _w, _src in token["expansions"]}
    for term, weight, source in M.weighted_variants(token["surface"], index, costs, k=k):
        if term not in seen:
            token["expansions"].append((term, round(weight, 4), source))
            seen.add(term)
    return token


def expand_query(query, index, costs, k=5):
    """Expand every token of a query object in place, then return it."""
    for token in query["tokens"]:
        expand_token(token, index, costs, k=k)
    return query
