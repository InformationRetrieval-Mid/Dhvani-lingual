"""Unit tests for TREC run pooling tool (dhvani/eval/pool.py)."""

from pathlib import Path
from dhvani.eval.pool import pool_runs


def test_pool_runs_basic(tmp_path: Path):
    run1 = tmp_path / "run1.txt"
    run2 = tmp_path / "run2.txt"

    run1.write_text(
        "N01 Q0 doc_1 1 0.95 bm25\n"
        "N01 Q0 doc_2 2 0.85 bm25\n"
        "N01 Q0 doc_3 3 0.75 bm25\n"
        "N02 Q0 doc_A 1 0.90 bm25\n",
        encoding="utf-8",
    )
    run2.write_text(
        "N01 Q0 doc_2 1 0.98 dense\n"
        "N01 Q0 doc_4 2 0.88 dense\n"
        "N02 Q0 doc_B 1 0.92 dense\n"
        "N02 Q0 doc_A 2 0.81 dense\n",
        encoding="utf-8",
    )

    pooled = pool_runs([str(run1), str(run2)], top_k=2)

    assert pooled["N01"] == {"doc_1", "doc_2", "doc_4"}
    assert pooled["N02"] == {"doc_A", "doc_B"}


def test_pool_runs_top_k_cutoff(tmp_path: Path):
    run = tmp_path / "run.txt"
    lines = [f"N01 Q0 doc_{i} {i} {1.0 - i * 0.05} run" for i in range(1, 20)]
    run.write_text("\n".join(lines) + "\n", encoding="utf-8")

    pooled = pool_runs([str(run)], top_k=5)
    assert len(pooled["N01"]) == 5
    assert pooled["N01"] == {f"doc_{i}" for i in range(1, 6)}
