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
    Load STRONG candidates from the analysis file.

    If the generated candidate file is unavailable,
    return an empty candidate set so that AUTO mode
    behaves like no stemming instead of breaking imports.
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

    using the light stem as the candidate class and requiring
    the canonical form itself to occur in the corpus.

    The canonical form is preferably the light stem itself.
    """
    auto_map = {}

    for stem_word, row in candidates.items():
        forms = parse_surface_forms(
            row["surface_forms"]
        )

        if len(forms) < 2:
            continue

        # The proposed lexical base must actually occur
        # in the corpus.
        base_frequency = corpus_frequencies.get(
            stem_word,
            0,
        )

        if base_frequency == 0:
            continue

        for surface_form in forms:
            if surface_form == stem_word:
                continue

            # Make sure this really belongs to the
            # candidate stem class.
            if stem(surface_form) != stem_word:
                continue

            auto_map[surface_form] = stem_word

    return auto_map


# These are safe to initialize even when the generated
# AUTO files do not exist.
#
# On a normal development machine with the generated
# files present, the full AUTO mapping is loaded.
#
# On a fresh checkout, both become empty and AUTO
# simply performs no selective stemming.
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

    If the generated AUTO files are unavailable,
    the word is returned unchanged.
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