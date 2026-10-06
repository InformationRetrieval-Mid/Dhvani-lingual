from text.normalize import normalize
from text.tokenize import tokenize
from text.stem import stem
from text.aggressive_stem import stem_aggressive


SUPPORTED_MODES = {"none", "light", "aggr"}


def analyze(text: str, mode: str) -> list[tuple[str, int]]:
    """
    Normalize, tokenize, and optionally stem text.

    Modes:
        none  - no stemming
        light - light Hindi stemming
        aggr  - aggressive Hindi stemming

    Returns:
        List of (term, position) tuples.
    """
    if mode not in SUPPORTED_MODES:
        raise ValueError(f"Unsupported analysis mode: {mode}")

    normalized = normalize(text)
    tokens = tokenize(normalized)

    analyzed = []

    for position, token in enumerate(tokens):
        if mode == "light":
            token = stem(token)
        elif mode == "aggr":
            token = stem_aggressive(token)

        analyzed.append((token, position))

    return analyzed