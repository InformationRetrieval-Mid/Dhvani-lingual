"""k-gram index over the vocabulary, for fast candidate generation.

Scoring a query word against every vocabulary term by edit distance is too slow.
A k-gram index narrows the field first: index the character k-grams of each term
(on its canonical Roman form, so Devanagari and Roman queries meet on common
ground), then for a query word return the terms that share the most k-grams,
ranked by Jaccard overlap. The matcher (`match.py`) re-ranks those few candidates
by edit distance.

Vocabulary source: Dhrithi's ``idx.vocab`` once it exists; until then, the
Aksharantar word list. Either way it is just an iterable of terms, so swapping
the source changes nothing here.
"""

from collections import defaultdict

from dhvani.query.langid import script
from dhvani.query.phonetics import dhvani_code
from dhvani.query.roman import romanize


def _canonical(word):
    """Canonical Roman form used for indexing and lookup."""
    return romanize(word) if script(word) == "devanagari" else word.lower()


def kgrams(text, k=2):
    """Character k-grams of ``text`` with boundary markers.

    The ``$`` markers make the first/last characters matter, so ``mausam`` and
    ``xmausam`` don't look identical at the edges.
    """
    s = "$" + text + "$"
    if len(s) <= k:
        return {s}
    return {s[i:i + k] for i in range(len(s) - k + 1)}


class KGramIndex:
    """Maps character k-grams to the vocabulary terms that contain them."""

    def __init__(self, vocab, k=2):
        self.k = k
        self.postings = defaultdict(set)   # k-gram -> {terms}
        self._grams = {}                   # term -> frozenset(k-grams)
        self._by_code = defaultdict(set)   # Dhvani-code -> {terms}
        for term in vocab:
            canonical = _canonical(term)
            grams = kgrams(canonical, k)
            self._grams[term] = grams
            for g in grams:
                self.postings[g].add(term)
            self._by_code[dhvani_code(canonical)].add(term)

    def phonetic_candidates(self, word):
        """Terms that share ``word``'s Dhvani-code, whatever their spelling.

        This is the safety net for phonetically-close but spelling-distant pairs
        like ``iyer`` / ``अय्यर`` (both code ``26``): their k-gram overlap is tiny,
        so k-gram search alone can drop the right term from the candidate pool
        before the matcher ever ranks it.
        """
        code = dhvani_code(_canonical(word))
        if not code:
            return set()
        return set(self._by_code.get(code, set()))

    def candidates(self, word, limit=50):
        """Return ``[(term, jaccard), ...]`` for the ``limit`` best matches.

        Only terms sharing at least one k-gram with ``word`` are considered;
        they are ranked by Jaccard overlap on the k-gram sets.
        """
        qg = kgrams(_canonical(word), self.k)
        pool = set()
        for g in qg:
            pool |= self.postings.get(g, set())

        scored = []
        for term in pool:
            tg = self._grams[term]
            jaccard = len(qg & tg) / len(qg | tg)
            scored.append((term, jaccard))
        scored.sort(key=lambda item: (-item[1], item[0]))
        return scored[:limit]
