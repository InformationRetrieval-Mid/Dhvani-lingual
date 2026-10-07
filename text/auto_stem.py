import csv
import json
from collections import Counter
from pathlib import Path

from text.normalize import normalize
from text.tokenize import tokenize
from text.stem import stem


AUTO_CANDIDATES_PATH = Path("data/auto_candidates.tsv")
CORPUS_PATH = Path("data/dev_news.jsonl")


REJECTED_STEMS = {
    "भार",
    "साम",
    "किय",
    "किस",
    "आन",
    "बार",
    "आग",
    "मंत्र",
    "जानकार",
    "मौक",
    "पीछ",
    "जी",
}


def load_corpus_forms():
    """
    Count the actual surface forms occurring in the corpus.

    The corpus is optional. If it is unavailable, return an
    empty frequency table so AUTO can still use the committed
    candidate configuration.
    """
    frequencies = Counter()

    if not CORPUS_PATH.exists():
        return frequencies

    with CORPUS_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        for line in file:
            if not line.strip():
                continue

            article = json.loads(line)

            text = (
                article.get("headline", "")
                + " "
                + article.get("body", "")
            )

            for token in tokenize(normalize(text)):
                frequencies[token] += 1

    return frequencies


def load_auto_candidates():
    """
    Load STRONG candidates from the approved AUTO configuration.

    The candidate file is intentionally allowed to be committed
    because it represents the approved selective-stemming
    configuration used by the project.
    """
    if not AUTO_CANDIDATES_PATH.exists():
        return {}

    candidates = {}

    with AUTO_CANDIDATES_PATH.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as file:
        reader = csv.DictReader(
            file,
            delimiter="\t",
        )

        for row in reader:
            if row["classification"] != "STRONG":
                continue

            stem_word = row["stem"]

            if stem_word in REJECTED_STEMS:
                continue

            candidates[stem_word] = row

    return candidates


def parse_surface_forms(surface_forms):
    """
    Parse:

        'दिक्कतें:20, दिक्कतों:15'

    into:

        {'दिक्कतें': 20, 'दिक्कतों': 15}
    """
    forms = {}

    for item in surface_forms.split(","):
        item = item.strip()

        if not item or ":" not in item:
            continue

        form, frequency = item.rsplit(":", 1)

        try:
            frequency = int(frequency)
        except ValueError:
            continue

        forms[form] = frequency

    return forms


def build_auto_map(candidates, corpus_frequencies):
    """
    Build:

        surface form -> canonical lexical form

    from the approved selective-stemming candidates.

    If the development corpus is available, the canonical form
    must also occur in that corpus.

    If the development corpus is unavailable, the committed
    candidate configuration is trusted directly.
    """
    auto_map = {}

    for stem_word, row in candidates.items():
        forms = parse_surface_forms(
            row["surface_forms"]
        )

        if len(forms) < 2:
            continue

        # If the corpus is available, keep the original
        # protection that the canonical form must occur in it.
        #
        # If the corpus is unavailable, the candidate file
        # itself is the approved configuration.
        if corpus_frequencies:
            base_frequency = corpus_frequencies.get(
                stem_word,
                0,
            )

            if base_frequency == 0:
                continue

        for surface_form in forms:
            if surface_form == stem_word:
                continue

            # Make sure the candidate still belongs to the
            # expected light-stem class.
            if stem(surface_form) != stem_word:
                continue

            auto_map[surface_form] = stem_word

    return auto_map


CORPUS_FREQUENCIES = load_corpus_forms()
AUTO_CANDIDATES = load_auto_candidates()

AUTO_MAP = build_auto_map(
    AUTO_CANDIDATES,
    CORPUS_FREQUENCIES,
)


def stem_auto(word: str) -> str:
    """
    Apply selective corpus-derived stemming.

    Only approved surface forms are changed.

    Example:

        दिक्कतें -> दिक्कत
        दिक्कतों -> दिक्कत
    """
    if not word:
        return word

    return AUTO_MAP.get(word, word)


def is_auto_stemmed(word: str) -> bool:
    return stem_auto(word) != word


def auto_stem_count():
    return len(AUTO_MAP)


if __name__ == "__main__":
    print(
        f"Approved stem classes: "
        f"{len(AUTO_CANDIDATES)}"
    )

    print(
        f"Approved surface-form mappings: "
        f"{len(AUTO_MAP)}"
    )

    examples = [
        "बारिश",
        "बारिशें",
        "दिक्कत",
        "दिक्कतें",
        "दिक्कतों",
        "विधानसभा",
        "विधानसभाओं",
        "समस्या",
        "समस्याओं",
        "पता",
        "पति",
        "भारी",
        "भारती",
    ]

    print()
    print("EXAMPLES")
    print("-" * 50)

    for word in examples:
        print(
            f"{word:<15} -> {stem_auto(word)}"
        )