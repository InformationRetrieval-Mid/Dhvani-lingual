"""Run every stemming mode x every ranker over every query and score it.

    python -m dhvani.eval.experiments
    python -m dhvani.eval.experiments --queries eval/queries.tsv --qrels eval/qrels_news.txt

For each (stemming mode, ranker) it writes a TREC run file, evaluates it
against the judgments, and prints:

- the full results table (P@10, R@10, MAP, nDCG@10), overall and per query form
- the stemming comparison: every stemming mode side by side for one ranker
- per-query wins and losses of each stemming mode against no stemming

Judgments are per information need, so every form of a need (Hindi,
Hinglish, English) is scored against the same judged articles.

Results go to data/eval/ (gitignored). Plots are drawn if matplotlib is
installed, otherwise skipped.
"""

import argparse
import csv
from collections import defaultdict
from pathlib import Path

from dhvani.eval.metrics import average_11_point, average_precision, evaluate, read_qrels, read_run, write_run
from dhvani.rank.parser import parse_and_rank
from dhvani.rank.query_stub import exact_query
from dhvani.rank.sample_index import SampleIndex
from dhvani.rank.speedups import (
    ChampionLists,
    ClusterPruning,
    ImpactOrdered,
    RecencyTiers,
    overlap_at_k,
    search_champions,
    search_clusters,
    search_impact,
    search_index_elimination,
    search_tiered,
)
from dhvani.rank.vsm import search
from dhvani.rank.xling import translate

SAMPLE_DIR = Path(__file__).resolve().parent / "sample"
OUT_DIR = Path(__file__).resolve().parents[2] / "data" / "eval"

STEM_MODES = ("none", "light", "aggr", "yass", "auto")
RANKERS = ("net", "lnc", "bm25")
METRICS_K = 10


def read_queries(path):
    """[(qid, need_id, form, text)] from a tab-separated file with a header."""
    rows = []
    with open(path, encoding="utf-8") as f:
        next(f, None)
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) == 4 and parts[0]:
                rows.append(tuple(parts))
    return rows


def build_query(text):
    """Query object the experiments use: exact matches plus English translations.

    Swap exact_query for Viraja's query layer once it's ready.
    """
    return translate(exact_query(text))


def default_loader(mode):
    # Swap for the real index once it's ready: return Index.load(mode), or
    # None for a mode that hasn't been built yet so it gets skipped.
    return SampleIndex.load(mode)


def run_one(index, queries, ranker, k=METRICS_K, query_builder=build_query):
    """{qid: [(doc_id, score), ...]} for one index and ranker."""
    out = {}
    for qid, _need, _form, text in queries:
        results = parse_and_rank(query_builder(text), index, k=k, ranker=ranker)
        out[qid] = [(doc_id, score) for doc_id, score, _ in results]
    return out


def score_run(run, queries, qrels, k=METRICS_K):
    """Mean metrics overall and per form, plus per-query AP.

    Returns {"all": means, "<form>": means, ...}, {qid: AP}.
    """
    rankings = {qid: [d for d, _ in res] for qid, res in run.items()}
    by_query = {qid: qrels.get(need, {}) for qid, need, _form, _ in queries}
    groups = {"all": [q[0] for q in queries]}
    for qid, _need, form, _ in queries:
        groups.setdefault(form, []).append(qid)
    table = {}
    for group, qids in groups.items():
        _, means = evaluate({q: rankings.get(q, []) for q in qids}, {q: by_query[q] for q in qids}, k=k)
        if means:
            table[group] = means
    per_query_ap = {qid: average_precision(rankings.get(qid, []), by_query[qid]) for qid in rankings}
    return table, per_query_ap


def run_experiments(queries, qrels, loader=default_loader, modes=STEM_MODES, rankers=RANKERS,
                    out_dir=OUT_DIR, k=METRICS_K, query_builder=build_query):
    """Run everything. Returns (results, per_query_ap, skipped_modes).

    results[(mode, ranker)] = {"all": means, "<form>": means}
    per_query_ap[(mode, ranker)] = {qid: AP}
    """
    out_dir = Path(out_dir)
    (out_dir / "runs").mkdir(parents=True, exist_ok=True)
    results, per_query_ap, skipped = {}, {}, []
    for mode in modes:
        index = loader(mode)
        if index is None:
            skipped.append(mode)
            continue
        for ranker in rankers:
            run = run_one(index, queries, ranker, k=k, query_builder=query_builder)
            write_run(out_dir / "runs" / f"{mode}_{ranker}.txt", run, f"{mode}_{ranker}")
            results[(mode, ranker)], per_query_ap[(mode, ranker)] = score_run(run, queries, qrels, k=k)
    return results, per_query_ap, skipped


def xling_comparison(queries, qrels, loader=default_loader, ranker="net", k=METRICS_K):
    """English queries with translation off vs on: {setup: means}."""
    english = [q for q in queries if q[2] == "english"]
    if not english:
        return {}
    index = loader("none")
    out = {}
    for name, builder in (("translation off", exact_query), ("dictionary translation", build_query)):
        run = run_one(index, english, ranker, k=k, query_builder=builder)
        table, _ = score_run(run, english, qrels, k=k)
        out[name] = table.get("all", {})
    return out


def speedup_table(queries, index, k=METRICS_K, query_builder=None, champion_r=(2, 5, 10, 50), cluster_b=(1, 3),
                  impact_docs=(20, 50), impact_share=(0.5,)):
    """Speed vs quality for the Lecture 7 speed-ups, against exact lnc.ltc.

    For each method: the mean share of candidate articles actually scored, and
    the mean share of the exact top k it kept (overlap@k). Lower "scored" is
    faster; higher "kept" is closer to the exact ranking.
    """
    query_builder = query_builder or build_query
    methods = [("index elimination", lambda q: search_index_elimination(q, index, k=k))]
    for r in champion_r:
        champs = ChampionLists(index, r=r)
        methods.append((f"champion lists, r={r}", lambda q, c=champs: search_champions(q, index, c, k=k)))
    tiers = RecencyTiers(index)
    methods.append(("recent-news tiers", lambda q: search_tiered(q, index, tiers, k=k)))
    clusters = ClusterPruning(index)
    for b in cluster_b:
        methods.append((f"cluster pruning, b={b}", lambda q, b=b: search_clusters(q, index, clusters, k=k, b=b)))
    impact = ImpactOrdered(index)
    for n in impact_docs:
        methods.append((f"impact-ordered, first {n}", lambda q, n=n: search_impact(q, index, impact, k=k, max_docs=n)))
    for share in impact_share:
        methods.append((f"impact-ordered, weight >= {share} x best",
                        lambda q, s=share: search_impact(q, index, impact, k=k, max_docs=None, min_share=s)))

    rows = []
    for name, run in methods:
        scored, kept, n = 0.0, 0.0, 0
        for _qid, _need, _form, text in queries:
            q = query_builder(text)
            exact = search(q, index, k=k)
            if not exact:
                continue
            fast, stats = run(q)
            scored += stats["scored"] / stats["full_candidates"] if stats["full_candidates"] else 0.0
            kept += overlap_at_k(fast, exact, k=k)
            n += 1
        if n:
            rows.append((name, scored / n, kept / n))
    return rows


def results_rows(results, k=METRICS_K):
    rows = []
    for (mode, ranker), groups in results.items():
        for group, m in groups.items():
            rows.append([mode, ranker, group, m[f"P@{k}"], m[f"R@{k}"], m["MAP"], m[f"nDCG@{k}"]])
    return rows


def stemming_comparison(results, ranker="net", group="all", k=METRICS_K):
    """[(mode, P@k, R@k, MAP, nDCG@k)] for one ranker and query form."""
    rows = []
    for (mode, r), groups in results.items():
        if r == ranker and group in groups:
            m = groups[group]
            rows.append((mode, m[f"P@{k}"], m[f"R@{k}"], m["MAP"], m[f"nDCG@{k}"]))
    return rows


def wins_and_losses(per_query_ap, ranker="net", baseline="none", tol=1e-9):
    """{mode: (wins, losses, ties, [(qid, delta)])} against the baseline mode."""
    base = per_query_ap.get((baseline, ranker), {})
    out = {}
    for (mode, r), aps in per_query_ap.items():
        if r != ranker or mode == baseline:
            continue
        deltas = [(q, aps[q] - base.get(q, 0.0)) for q in aps]
        wins = sum(1 for _, d in deltas if d > tol)
        losses = sum(1 for _, d in deltas if d < -tol)
        out[mode] = (wins, losses, len(deltas) - wins - losses, sorted(deltas, key=lambda x: x[1]))
    return out


def plot_pr_curves(queries, qrels, out_dir=OUT_DIR, ranker="net"):
    """Averaged 11-point PR curve per stemming mode. Skipped without matplotlib."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return None
    by_query = {qid: qrels.get(need, {}) for qid, need, _f, _ in queries}
    fig, ax = plt.subplots(figsize=(6, 4.5))
    levels = [i / 10 for i in range(11)]
    for path in sorted(Path(out_dir, "runs").glob(f"*_{ranker}.txt")):
        mode = path.stem.rsplit("_", 1)[0]
        curve = average_11_point(read_run(path), by_query)
        ax.plot(levels, curve, marker="o", label=mode)
    ax.set_xlabel("Recall")
    ax.set_ylabel("Interpolated precision")
    ax.set_title(f"11-point interpolated PR, {ranker}")
    ax.set_ylim(0, 1.05)
    ax.legend()
    ax.grid(alpha=0.3)
    out = Path(out_dir) / f"pr_curves_{ranker}.png"
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return out


def _print_table(headers, rows):
    cells = [[(f"{c:.4f}" if isinstance(c, float) else str(c)) for c in row] for row in rows]
    widths = [max(len(h), *(len(r[i]) for r in cells)) if cells else len(h) for i, h in enumerate(headers)]
    print("  ".join(h.ljust(w) for h, w in zip(headers, widths)))
    print("  ".join("-" * w for w in widths))
    for r in cells:
        print("  ".join(c.ljust(w) for c, w in zip(r, widths)))


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run every stemming mode and ranker, then evaluate.")
    parser.add_argument("--queries", default=SAMPLE_DIR / "queries.tsv")
    parser.add_argument("--qrels", default=SAMPLE_DIR / "qrels.txt")
    parser.add_argument("--out", default=OUT_DIR)
    parser.add_argument("--ranker", default="net", help="ranker for the stemming comparison table")
    args = parser.parse_args(argv)

    queries = read_queries(args.queries)
    qrels = read_qrels(args.qrels)
    results, per_query_ap, skipped = run_experiments(queries, qrels, out_dir=args.out)

    k = METRICS_K
    print(f"{len(queries)} queries, {len(qrels)} judged information needs")
    if skipped:
        print("Skipped (not built yet):", ", ".join(skipped))

    print("\nAll results")
    rows = results_rows(results)
    _print_table(["stemming", "ranker", "queries", f"P@{k}", f"R@{k}", "MAP", f"nDCG@{k}"], rows)
    with open(Path(args.out) / "results.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["stemming", "ranker", "queries", f"P@{k}", f"R@{k}", "MAP", f"nDCG@{k}"])
        w.writerows(rows)

    print(f"\nStemming comparison ({args.ranker}, all queries)")
    _print_table(["stemming", f"P@{k}", f"R@{k}", "MAP", f"nDCG@{k}"], stemming_comparison(results, args.ranker))

    print(f"\nPer-query wins and losses against no stemming ({args.ranker}, by AP)")
    for mode, (wins, losses, ties, _) in wins_and_losses(per_query_ap, args.ranker).items():
        print(f"{mode:<6} {wins} better, {losses} worse, {ties} same")

    xling = xling_comparison(queries, qrels, ranker=args.ranker)
    if xling:
        print(f"\nCross-lingual: English queries, translation off vs on ({args.ranker})")
        _print_table(["setup", f"P@{k}", f"R@{k}", "MAP", f"nDCG@{k}"],
                     [(name, m[f"P@{k}"], m[f"R@{k}"], m["MAP"], m[f"nDCG@{k}"]) for name, m in xling.items() if m])

    speed = speedup_table(queries, default_loader("none"))
    if speed:
        print(f"\nSpeed-ups vs exact lnc.ltc (mean over queries, k = {k})")
        _print_table(["method", "share scored", f"top-{k} kept"], speed)
        with open(Path(args.out) / "speedups.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["method", "share_scored", f"top{k}_kept"])
            w.writerows(speed)

    plot = plot_pr_curves(queries, qrels, args.out, args.ranker)
    print(f"\nPR curves: {plot}" if plot else "\nPR curves skipped: matplotlib isn't installed")
    print(f"Run files and results.csv are in {args.out}")


if __name__ == "__main__":
    main()
