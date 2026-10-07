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


def expand_token(token, index, costs, k=5):
    """Append up to ``k`` phonetic variants to one token's ``expansions`` list.

    Variants whose term is already present (the exact surface, or an expansion
    added earlier) are skipped, so weights never double up.
    """
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
