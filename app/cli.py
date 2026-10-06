"""Search from the terminal, with an optional step-by-step explanation.

    python app/cli.py "दिल्ली बारिश"
    python app/cli.py "दिल्ली बारिश" --explain
    python app/cli.py "कोहली शतक" --ranker bm25 --k 3 --explain

--explain prints every stage of the pipeline: the query object, the
query vector with its tf, df, idf and weights, the postings each term
touched, how many documents became candidates, the heap's top K, and a
score breakdown for each result.
"""

import argparse
import math
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dhvani.rank.bm25 import B, K1, bm25_scores, doc_lengths, idf as bm25_idf, search_bm25  # noqa: E402
from dhvani.rank.parser import STAGE_LABELS, parse_and_rank, stage_matches  # noqa: E402
from dhvani.rank.query_stub import exact_query  # noqa: E402
from dhvani.rank.sample_index import SampleIndex  # noqa: E402
from dhvani.rank.scoring import DEFAULT_WEIGHTS, rank  # noqa: E402
from dhvani.rank.vsm import ZONES, cosine_scores, log_tf, query_vector, search  # noqa: E402

RANKERS = ("net", "lnc", "bm25")
MAX_POSTINGS_SHOWN = 6


def load_index(mode):
    # Swap this for the real index once it's ready: Index.load(mode).
    return SampleIndex.load(mode)


def heading(out, title):
    out.append("")
    out.append(title)
    out.append("-" * len(title))


def table(out, headers, rows):
    """Plain left-aligned table, wide enough for every cell."""
    cols = list(zip(headers, *rows)) if rows else [[h] for h in headers]
    widths = [max(len(str(c)) for c in col) for col in cols]
    out.append("  ".join(str(h).ljust(w) for h, w in zip(headers, widths)))
    out.append("  ".join("-" * w for w in widths))
    for row in rows:
        out.append("  ".join(str(c).ljust(w) for c, w in zip(row, widths)))


def explain_query(out, query):
    heading(out, "1. Query object")
    rows = []
    for tok in query["tokens"]:
        lang = ", ".join(f"{k} {v:.2f}" for k, v in tok["lang"].items() if v)
        exps = ", ".join(f"{t} ({w:.2f}, {s})" for t, w, s in tok["expansions"])
        rows.append((tok["surface"], tok["script"], lang, exps))
    table(out, ("token", "script", "language", "expands to"), rows)


def explain_query_vector(out, query, index, ranker):
    if ranker == "bm25":
        heading(out, f"2. Query terms (BM25, k1 = {K1}, b = {B})")
        lengths = doc_lengths(index)
        avgdl = sum(lengths.values()) / len(lengths)
        out.append(f"N = {index.N}, average article length = {avgdl:.1f} tokens")
        weights = defaultdict(float)
        for tok in query["tokens"]:
            for term, w, _ in tok["expansions"]:
                weights[term] += w
        rows = []
        for term, w in weights.items():
            df = index.df(term)
            idf = f"{bm25_idf(df, index.N):.4f}" if df else "not in index"
            rows.append((term, f"{w:.2f}", df, idf))
        table(out, ("term", "query weight", "df", "idf = ln(1 + (N - df + 0.5) / (df + 0.5))"), rows)
        return

    heading(out, "2. Query vector (ltc: log tf x idf, then cosine-normalised)")
    out.append(f"N = {index.N}")
    qtf = defaultdict(float)
    for tok in query["tokens"]:
        for term, w, _ in tok["expansions"]:
            qtf[term] += w
    qvec = query_vector(query, index)
    rows = []
    for term, tf in qtf.items():
        df = index.df(term)
        if not df:
            rows.append((term, f"{tf:.2f}", 0, "-", "-", "dropped, not in index"))
            continue
        idf = math.log10(index.N / df)
        tf_w = log_tf(tf) if tf >= 1 else tf
        rows.append((term, f"{tf:.2f}", df, f"{idf:.4f}", f"{tf_w * idf:.4f}", f"{qvec[term]:.4f}"))
    table(out, ("term", "qtf", "df", "idf = log10(N/df)", "tf x idf", "normalised"), rows)


def explain_postings(out, query, index):
    heading(out, "3. Postings touched")
    terms = []
    for tok in query["tokens"]:
        for term, _, _ in tok["expansions"]:
            if term not in terms:
                terms.append(term)
    for term in terms:
        for zone in ZONES:
            plist = index.postings(term, zone)
            if not plist:
                continue
            shown = ", ".join(f"{d} tf={tf} pos={pos}" for d, tf, pos in plist[:MAX_POSTINGS_SHOWN])
            more = f", ... {len(plist) - MAX_POSTINGS_SHOWN} more" if len(plist) > MAX_POSTINGS_SHOWN else ""
            out.append(f"{term} [{zone}] ({len(plist)}): {shown}{more}")


def explain_candidates(out, query, index, ranker, k):
    heading(out, "4. Candidates and top K")
    if ranker == "bm25":
        scores, _ = bm25_scores(query, index)
    else:
        scores, _ = cosine_scores(query, index)
    out.append(f"{len(scores)} of {index.N} articles share at least one query term, so only those get scored.")
    out.append(f"The heap keeps the best {k} instead of sorting all {len(scores)}.")


def explain_parser(out, query, index, k):
    heading(out, "4b. Query parser (strictest stage first, stop once there are k)")
    found = set()
    for stage, docs in stage_matches(index, query):
        new = docs - found
        found |= docs
        out.append(f"{STAGE_LABELS[stage]:<26} {len(docs):>3} articles, {len(new):>3} new, {len(found):>3} so far")
        if len(found) >= k:
            out.append(f"Stopped here: {len(found)} >= k = {k}.")
            break


def explain_result(out, i, doc_id, score, explain, index, ranker):
    article = getattr(index, "articles", {}).get(doc_id, {})
    meta = index.meta[doc_id]
    out.append("")
    stage = explain.get("stage")
    out.append(f"#{i}  {doc_id}  score {score:.4f}" + (f"  [{STAGE_LABELS[stage]}]" if stage else ""))
    if article:
        out.append(f"    {article['headline']}")
    out.append(f"    {meta.get('source')} · {meta.get('section')} · {(meta.get('date') or '')[:10]}")
    terms = explain.get("terms", explain)
    if ranker == "net":
        w = DEFAULT_WEIGHTS
        out.append(f"    cosine            {explain['cosine']:.4f}")
        for term, part in terms.items():
            out.append(f"      {term:<14}  {part:.4f}")
        out.append(f"    + {w['zone']} x zone      {explain['zone']:.4f}")
        out.append(f"    + {w['prox']} x proximity {explain['proximity']:.4f}")
        out.append(f"    + {w['recency']} x recency   {explain['recency']:.4f}")
        out.append(f"    = net score       {explain['net']:.4f}")
    else:
        label = "BM25 contribution" if ranker == "bm25" else "cosine contribution"
        for term, part in terms.items():
            out.append(f"      {term:<14}  {part:.4f}  ({label})")


def run(argv=None):
    parser = argparse.ArgumentParser(description="Search Dhvani from the terminal.")
    parser.add_argument("query", help="what to search for")
    parser.add_argument("--ranker", choices=RANKERS, default="net", help="net (default), lnc or bm25")
    parser.add_argument("--k", type=int, default=5, help="how many results to show")
    parser.add_argument("--stem", default="none", help="which index to use: none, light or auto")
    parser.add_argument("--explain", action="store_true", help="print every stage of the pipeline")
    parser.add_argument("--no-parser", action="store_true",
                        help="skip the query parser and rank every article that shares a word")
    args = parser.parse_args(argv)

    index = load_index(args.stem)
    query = exact_query(args.query)
    out = [f'Query: "{args.query}"   ranker: {args.ranker}   index: {args.stem}   k: {args.k}']

    if args.explain:
        explain_query(out, query)
        explain_query_vector(out, query, index, args.ranker)
        explain_postings(out, query, index)
        explain_candidates(out, query, index, args.ranker, args.k)
        if not args.no_parser:
            explain_parser(out, query, index, args.k)

    if not args.no_parser:
        results = parse_and_rank(query, index, k=args.k, ranker=args.ranker)
    elif args.ranker == "net":
        results = rank(query, index, k=args.k)
    elif args.ranker == "lnc":
        results = search(query, index, k=args.k)
    else:
        results = search_bm25(query, index, k=args.k)

    heading(out, "5. Results" if args.explain else "Results")
    if not results:
        out.append("No matches.")
    for i, (doc_id, score, explain) in enumerate(results, start=1):
        if args.explain:
            explain_result(out, i, doc_id, score, explain, index, args.ranker)
        else:
            headline = getattr(index, "articles", {}).get(doc_id, {}).get("headline", "")
            stage = explain.get("stage")
            tag = f"  [{STAGE_LABELS[stage]}]" if stage else ""
            out.append(f"{i}. {score:.4f}  {doc_id}  {headline}{tag}")

    text = "\n".join(out)
    print(text)
    return text


if __name__ == "__main__":
    run()
