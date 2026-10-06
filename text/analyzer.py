from text.normalize import normalize
from text.tokenize import tokenize
from text.stem import stem


def analyze(text: str, mode: str) -> list[tuple[str, int]]:
    """
    Normalize, tokenize, and optionally stem text.

    Returns:
        List of (term, position) tuples.
    """

    if mode not in {"none", "light"}:
        raise ValueError(f"Unsupported analysis mode: {mode}")

    normalized = normalize(text)
    tokens = tokenize(normalized)

    analyzed = []

    for position, token in enumerate(tokens):
        if mode == "light":
            token = stem(token)

        analyzed.append((token, position))

    return analyzed