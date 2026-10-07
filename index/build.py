import argparse
import json
from pathlib import Path

from index.positional import Index


REQUIRED_FIELDS = (
    "doc_id",
    "headline",
    "body",
)

METADATA_FIELDS = (
    "source",
    "date",
    "state",
    "city",
    "section",
    "dup_of",
    "links",
)

SUPPORTED_MODES = (
    "none",
    "light",
    "aggr",
)


def iter_articles(path):
    """Read articles from a JSONL file one article at a time."""

    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(
            f"Article file not found: {path}"
        )

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
                        f"Line {line_number}: "
                        f"missing required field '{field}'"
                    )

            if not isinstance(article["doc_id"], str):
                raise ValueError(
                    f"Line {line_number}: "
                    f"'doc_id' must be a string"
                )

            if not isinstance(article["headline"], str):
                raise ValueError(
                    f"Line {line_number}: "
                    f"'headline' must be a string"
                )

            if not isinstance(article["body"], str):
                raise ValueError(
                    f"Line {line_number}: "
                    f"'body' must be a string"
                )

            yield article


def build_index(input_path, mode, output_path=None):
    """Build one positional index from the JSONL corpus."""

    if mode not in SUPPORTED_MODES:
        raise ValueError(
            f"Unsupported index mode: {mode}. "
            f"Currently supported modes are: "
            f"{', '.join(SUPPORTED_MODES)}."
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
        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        index.save(output_path)

    return index


def build_indexes(input_path="data/news.jsonl"):
    """Build all currently supported index variants."""

    indexes = {}

    for mode in SUPPORTED_MODES:
        indexes[mode] = build_index(
            input_path=input_path,
            mode=mode,
        )

    return indexes


def main():

    parser = argparse.ArgumentParser(
        description=(
            "Build a Dhvani positional index "
            "from a JSONL corpus."
        )
    )

    parser.add_argument(
        "--input",
        default="data/news.jsonl",
        help="Path to the article JSONL file.",
    )

    parser.add_argument(
        "--mode",
        choices=(*SUPPORTED_MODES, "both"),
        default="both",
        help="Indexing mode to build.",
    )

    parser.add_argument(
        "--output",
        default=None,
        help=(
            "Optional output path when building "
            "a single index mode."
        ),
    )

    args = parser.parse_args()

    if args.mode == "both":

        if args.output is not None:
            parser.error(
                "--output can only be used "
                "with a single index mode"
            )

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