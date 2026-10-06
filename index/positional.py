import pickle
from collections import defaultdict
from pathlib import Path

from text.analyzer import analyze


def _zone_postings():
    """
    Create the zone structure used by the inverted index.
    Kept as a top-level function so the index can be pickled.
    """
    return {
        "headline": [],
        "body": [],
    }


class Index:
    """
    Positional inverted index for one analysis mode.

    Supported modes:
        none
        light

    postings:
        term -> zone -> list of (doc_id, tf, positions)

    meta:
        doc_id -> document metadata

    N:
        Number of indexed documents

    vocab:
        Set of indexed terms

    doc_norm:
        Document normalization values used later by scoring.
    """

    INDEX_DIR = Path("indexes")

    def __init__(self, mode: str):
        if mode not in {"none", "light"}:
            raise ValueError(f"Unsupported index mode: {mode}")

        self.mode = mode

        self.postings = defaultdict(_zone_postings)

        self.meta = {}
        self.N = 0
        self.vocab = set()
        self.doc_norm = {}

    def add_document(
        self,
        doc_id: str,
        headline: str,
        body: str,
        metadata: dict,
    ):
        """
        Add one document to the index.
        """

        if doc_id in self.meta:
            raise ValueError(f"Document already indexed: {doc_id}")

        self.meta[doc_id] = metadata
        self.N += 1

        self._add_zone(doc_id, headline, "headline")
        self._add_zone(doc_id, body, "body")

    def _add_zone(self, doc_id: str, text: str, zone: str):
        """
        Analyze one document zone and add positional postings.
        """

        if zone not in {"headline", "body"}:
            raise ValueError(f"Unsupported zone: {zone}")

        analyzed = analyze(text, self.mode)

        term_positions = defaultdict(list)

        for term, position in analyzed:
            term_positions[term].append(position)

        for term, positions in term_positions.items():
            self.postings[term][zone].append(
                (doc_id, len(positions), positions)
            )

            self.vocab.add(term)

    def postings_for(self, term: str, zone: str):
        """
        Return postings for a term in a particular zone.
        """

        if zone not in {"headline", "body"}:
            raise ValueError(f"Unsupported zone: {zone}")

        return self.postings.get(term, {}).get(zone, [])

    def df(self, term: str) -> int:
        """
        Return document frequency across headline and body.

        A document containing the term in both zones is counted once.
        """

        doc_ids = set()

        for zone in ("headline", "body"):
            for doc_id, _, _ in self.postings.get(term, {}).get(zone, []):
                doc_ids.add(doc_id)

        return len(doc_ids)

    def save(self, path=None):
        """
        Save the index to disk.

        If no path is supplied, use:
            indexes/{mode}.pkl
        """

        if path is None:
            self.INDEX_DIR.mkdir(parents=True, exist_ok=True)
            path = self.INDEX_DIR / f"{self.mode}.pkl"

        with open(path, "wb") as f:
            pickle.dump(self, f)

    @classmethod
    def load(cls, mode: str):
        """
        Load an index using the shared project interface.

        Example:
            Index.load("none")
            Index.load("light")
        """

        if mode not in {"none", "light"}:
            raise ValueError(f"Unsupported index mode: {mode}")

        path = cls.INDEX_DIR / f"{mode}.pkl"

        if not path.exists():
            raise FileNotFoundError(
                f"Index file not found: {path}"
            )

        with open(path, "rb") as f:
            index = pickle.load(f)

        if not isinstance(index, cls):
            raise TypeError("Loaded file does not contain an Index")

        if index.mode != mode:
            raise ValueError(
                f"Index mode mismatch: expected {mode}, "
                f"found {index.mode}"
            )

        return index