"""TREC Run Pooling Tool (Format 5 in formats.md)."""

import argparse
from pathlib import Path
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

    pools = pool_runs(args.runs, top_k=args.top_k)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    total_pairs = 0
    with open(out_path, "w", encoding="utf-8") as f:
        for qid in sorted(pools.keys()):
            for doc_id in sorted(pools[qid]):
                f.write(f"{qid} 0 {doc_id} 0\n")
                total_pairs += 1

    print(f"Pooled {total_pairs} query-doc pairs across {len(pools)} topics into {args.out}")


if __name__ == "__main__":
    main()


