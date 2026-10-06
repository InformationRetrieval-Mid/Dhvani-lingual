import argparse
import json
from pathlib import Path

from index.positional import Index


REQUIRED_FIELDS = ("doc_id", "headline", "body")
METADATA_FIELDS = ("source", "date", "state", "section", "dup_of")


def iter_articles(path):
    """
    Read articles from a JSONL file one article at a time.

    Blank lines are ignored.

    Raises:
        ValueError: if a line contains invalid JSON or is missing
                    a required field.
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Article file not found: {path}")

    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue

            try:
                article = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Line {line_number}: invalid JSON"
                ) from exc

            if not isinstance(article, dict):
                raise ValueError(
                    f"Line {line_number}: article must be a JSON object"
                )

            for field in REQUIRED_FIELDS:
                if field not in article:
                    raise ValueError(
                        f"Line {line_number}: missing required field '{field}'"
                    )

            if not isinstance(article["doc_id"], str):
                raise ValueError(
                    f"Line {line_number}: 'doc_id' must be a string"
                )

            if not isinstance(article["headline"], str):
                raise ValueError(
                    f"Line {line_number}: 'headline' must be a string"
                )

            if not isinstance(article["body"], str):
                raise ValueError(
                    f"Line {line_number}: 'body' must be a string"
                )

            yield article


def build_index(input_path, mode, output_path=None):
    """
    Build one positional index from a JSONL article corpus.

    Args:
        input_path: Path to data/news.jsonl.
        mode: Analyzer mode, currently "none" or "light".
        output_path: Optional path for the resulting pickle index.

    Returns:
        The populated Index object.
    """
    if mode not in {"none", "light"}:
        raise ValueError(
            f"Unsupported index mode: {mode}. "
            "Currently supported modes are 'none' and 'light'."
        )

    index = Index(mode)

    for article in iter_articles(input_path):
        metadata = {
            field: article.get(field)
            for field in METADATA_FIELDS
        }

        index.add_document(
            doc_id=article["doc_id"],
            headline=article["headline"],
            body=article["body"],
            metadata=metadata,
        )

    if output_path is None:
        index.save()
    else:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        index.save(output_path)

    return index


def build_indexes(input_path="data/news.jsonl"):
    """
    Build both currently supported indexes:

        indexes/none.pkl
        indexes/light.pkl

    Returns:
        Dictionary mapping mode -> Index.
    """
    indexes = {}

    for mode in ("none", "light"):
        indexes[mode] = build_index(input_path, mode)

    return indexes


def main():
    parser = argparse.ArgumentParser(
        description="Build a Dhvani positional index from a JSONL corpus."
    )

    parser.add_argument(
        "--input",
        default="data/news.jsonl",
        help="Path to the article JSONL file.",
    )

    parser.add_argument(
        "--mode",
        choices=("none", "light", "both"),
        default="both",
        help="Indexing mode to build.",
    )

    parser.add_argument(
        "--output",
        default=None,
        help="Optional output path when building a single index.",
    )

    args = parser.parse_args()

    if args.mode == "both":
        if args.output is not None:
            parser.error("--output can only be used with --mode none or --mode light")

        indexes = build_indexes(args.input)

        for mode, index in indexes.items():
            print(
                f"Built {mode} index: "
                f"{index.N} documents, "
                f"{len(index.vocab)} vocabulary terms"
            )

    else:
        index = build_index(
            input_path=args.input,
            mode=args.mode,
            output_path=args.output,
        )

        print(
            f"Built {args.mode} index: "
            f"{index.N} documents, "
            f"{len(index.vocab)} vocabulary terms"
        )


if __name__ == "__main__":
    main()