"""Load the Aksharantar Hindi dataset and export the pairs this layer needs.

Aksharantar (`ai4bharat/Aksharantar`, config ``hin``) is a transliteration
dataset: each row has a Devanagari ``native word`` and a human ``english word``
(its romanisation). From it we build two things:

* **training pairs** for the learned edit distance — ``(canonical, human)`` where
  ``canonical = romanize(native word)`` and ``human`` is the dataset's
  romanisation. Written to ``data/aksharantar/train_pairs.tsv``.
* **a test set** for the word-level matching evaluation — ``(native word,
  human romanisation)``. Written to ``data/aksharantar/test_pairs.tsv``.

The raw dataset and these files live under ``data/`` (git-ignored). Only code
goes on GitHub.

Run once after installing ``datasets``::

    python -m dhvani.query.aksharantar --max-train 50000 --max-test 5000
"""

import argparse
import os

from dhvani.query.roman import romanize

OUT_DIR = os.path.join("data", "aksharantar")


def _load_split(split, limit):
    from datasets import load_dataset  # imported lazily so the package stays light

    ds = load_dataset("ai4bharat/Aksharantar", "hin", split=split, streaming=True)
    rows = []
    for row in ds:
        native = (row.get("native word") or row.get("native_word") or "").strip()
        roman = (row.get("english word") or row.get("english_word") or "").strip().lower()
        if native and roman:
            rows.append((native, roman))
        if limit and len(rows) >= limit:
            break
    return rows


def _write_tsv(path, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        for a, b in rows:
            fh.write(f"{a}\t{b}\n")


def load_pairs(path):
    """Read a ``a<TAB>b`` TSV written by this module; returns ``[(a, b), ...]``."""
    pairs = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            parts = line.rstrip("\n").split("\t")
            if len(parts) == 2 and parts[0] and parts[1]:
                pairs.append((parts[0], parts[1]))
    return pairs


def main(argv=None):
    ap = argparse.ArgumentParser(description="Export Aksharantar Hindi pairs.")
    ap.add_argument("--max-train", type=int, default=50000)
    ap.add_argument("--max-test", type=int, default=5000)
    ap.add_argument("--out-dir", default=OUT_DIR)
    args = ap.parse_args(argv)

    train = _load_split("train", args.max_train)
    # canonical romanisation vs the dataset's human romanisation.
    train_pairs = [(romanize(native), roman) for native, roman in train]
    train_path = os.path.join(args.out_dir, "train_pairs.tsv")
    _write_tsv(train_path, train_pairs)
    print(f"wrote {len(train_pairs)} training pairs -> {train_path}")

    for split in ("test", "validation"):
        try:
            test = _load_split(split, args.max_test)
        except Exception:
            continue
        test_path = os.path.join(args.out_dir, "test_pairs.tsv")
        _write_tsv(test_path, test)  # (native word, human romanisation)
        print(f"wrote {len(test)} test pairs ({split}) -> {test_path}")
        break
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
