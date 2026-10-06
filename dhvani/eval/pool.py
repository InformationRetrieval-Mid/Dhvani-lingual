"""TREC Run Pooling Tool (Format 5 in formats.md)."""

import argparse
from typing import Dict, List, Set


def pool_runs(run_files: List[str], top_k: int = 10) -> Dict[str, Set[str]]:
    """Pool top-k document IDs per query ID across multiple TREC run files."""
    pools: Dict[str, Set[str]] = {}
    for run_path in run_files:
        with open(run_path, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) >= 6:
                    qid, _, doc_id, rank, score, _ = parts[:6]
                    if int(rank) <= top_k:
                        pools.setdefault(qid, set()).add(doc_id)
    return pools


def main():
    parser = argparse.ArgumentParser(description="Pool TREC run files for relevance judgment")
    parser.add_argument("--runs", nargs="+", required=True, help="List of TREC run files")
    parser.add_argument("--top-k", type=int, default=10, help="Top-K cutoff for pooling")
    parser.add_argument("--out", type=str, default="data/judgments_pool.txt", help="Output judgment file")
    args = parser.parse_args()


if __name__ == "__main__":
    main()
