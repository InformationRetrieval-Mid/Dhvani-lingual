"""Building the query object the ranker scores (format 4 in documentation/formats.md).

``build_query`` is Viraja's half of the Viraja -> Rishit handoff. Right now it
does **exact matching only**: every word expands to itself with weight 1.0 and
source "exact". That is the H3 deliverable — a query stub Rishit can score
against the real query format from day one, replacing his temporary
``dhvani/rank/query_stub.py``.

Phonetic and cross-lingual expansions (candidates from the k-gram index,
re-ranked by edit distance; English words translated via MUSE) get added here in
later phases, as extra entries in each token's ``expansions`` list. The *shape*
of the object does not change, so Rishit's ranker keeps working as we grow it.
"""

from dhvani.query import langid
from dhvani.query.tokenize import word_tokens


def build_query(raw):
    """Turn a raw query string into a query object (format 4), exact-match only.

    Returns::

        {"raw": raw,
         "tokens": [
            {"surface": <word>,
             "script": "devanagari" | "roman",
             "lang": {"hi": .., "hinglish": .., "en": ..},
             "expansions": [(<term>, <weight>, <source>), ...]},
            ...]}

    where ``source`` is one of "exact", "phonetic", "xling". For now the only
    expansion per token is the word itself: ``(word, 1.0, "exact")``.
    """
    tokens = []
    for word in word_tokens(raw):
        tokens.append({
            "surface": word,
            "script": langid.script(word),
            "lang": langid.classify(word),
            "expansions": [(word, 1.0, "exact")],
        })
    return {"raw": raw, "tokens": tokens}
