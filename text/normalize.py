import unicodedata


def normalize(text: str) -> str:
    """
    Normalize Hindi/Hinglish text before tokenization.

    Normalization performed:
    1. Unicode NFC normalization
    2. Remove zero-width joiner/non-joiner characters
    3. Normalize the common spelling variant "हिंदी" -> "हिन्दी"
    4. Normalize whitespace

    The goal is to reduce superficial spelling/encoding variation
    without performing stemming or tokenization.
    """

    # 1. Unicode canonical normalization
    text = unicodedata.normalize("NFC", text)

    # 2. Remove invisible zero-width characters.
    text = text.replace("\u200c", "")
    text = text.replace("\u200d", "")

    # 3. Fold the common spelling variant.
    text = text.replace("हिंदी", "हिन्दी")

    # 4. Collapse repeated whitespace and remove leading/trailing spaces.
    text = " ".join(text.split())

    return text