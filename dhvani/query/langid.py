"""Per-word language identification for a mixed Hindi / Hinglish / English query.

A Dhvani query can mix three ways of writing the same thing: Devanagari Hindi
(``मौसम``), romanised Hindi a.k.a. Hinglish (``mausam``) and English
(``weather``). We label each *word* on its own, because one query often mixes
them: ``kal ka weather``.

The label is a weight over three readings ``{"hi", "hinglish", "en"}`` and these
feed the query object (format 4). The plan calls out that some words — "main",
"to", "hi" — are valid English words *and* common romanised Hindi, so instead of
forcing a choice we keep both readings with weights and let the ranker sort it
out downstream.

Scope: this is a light, lexicon-based identifier, not a trained classifier. The
word lists below are deliberately small seeds, kept in one place so they are
easy to grow as we see more queries.
"""

# Devanagari block is U+0900..U+097F (plus extensions we do not need here).
_DEVA_START, _DEVA_END = "ऀ", "ॿ"

# Words that are ordinary English *and* common romanised Hindi. We refuse to
# guess and carry both readings. (Romanised Hindi gloss in the comment.)
AMBIGUOUS = {
    "main",  # English "main"      vs मैं "I"
    "to",    # English "to"        vs तो "then/so"
    "hi",    # English "hi"        vs ही "only/just"
    "is",    # English "is"        vs इस "this"
    "me",    # English "me"        vs में "in"
    "us",    # English "us"        vs उस "that"
    "do",    # English "do"        vs दो "two/give"
    "he",    # English "he"        vs हे "O! (vocative)"
    "the",   # English "the"       vs थे "were"
    "or",    # English "or"        vs और "and" (often typed "or")
}

# A small seed of clearly-English words we expect in news queries. Not in
# AMBIGUOUS, so these lean English.
ENGLISH = {
    "weather", "tomorrow", "today", "yesterday", "news", "election", "elections",
    "cricket", "match", "rain", "price", "prices", "market", "stock", "result",
    "results", "school", "schools", "holiday", "budget", "government", "minister",
    "prime", "police", "flood", "monsoon", "temperature", "forecast", "and", "of",
    "in", "on", "for", "with", "from", "what", "when", "where", "which", "latest",
}


def script(word):
    """"devanagari" if the word contains any Devanagari character, else "roman"."""
    for ch in word:
        if _DEVA_START <= ch <= _DEVA_END:
            return "devanagari"
    return "roman"


def classify(word):
    """Return a language-weight dict ``{"hi", "hinglish", "en"}`` for one word.

    - Devanagari  -> certainly Hindi.
    - Ambiguous   -> split evenly between a romanised-Hindi and an English reading.
    - Known English -> mostly English, a little romanised-Hindi mass kept for safety.
    - Anything else in Roman -> treated as romanised Hindi, the common case in a
      Hindi-news engine, with a little English mass kept.

    The small residual mass (0.1) on the losing reading mirrors the hedge in the
    format example (``mosam`` -> hinglish 0.9, en 0.1): it keeps a backup reading
    alive rather than zeroing it out.
    """
    word = word.lower()

    if script(word) == "devanagari":
        return {"hi": 1.0, "hinglish": 0.0, "en": 0.0}

    if word in AMBIGUOUS:
        return {"hi": 0.0, "hinglish": 0.5, "en": 0.5}

    if word in ENGLISH:
        return {"hi": 0.0, "hinglish": 0.1, "en": 0.9}

    return {"hi": 0.0, "hinglish": 0.9, "en": 0.1}
