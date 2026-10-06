"""Dhvani search app.

Run from the repo root:
    streamlit run app/streamlit_app.py

Every query runs against three indexes side by side: no stemming, stemming,
and auto (stem a word only when it helps). Until the real indexes are ready
all three columns use the sample index, so they'll look the same.
"""

import html
import sys
from pathlib import Path

import regex
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dhvani.rank.bm25 import search_bm25  # noqa: E402
from dhvani.rank.filters import field_values, make_filter  # noqa: E402
from dhvani.rank.query_stub import exact_query  # noqa: E402
from dhvani.rank.sample_index import SampleIndex, tokenize  # noqa: E402
from dhvani.rank.scoring import rank  # noqa: E402
from dhvani.rank.vsm import search  # noqa: E402

MODES = [("none", "No stemming"), ("light", "Stemming"), ("auto", "Auto")]

RANKERS = {
    "Net score (lnc.ltc + zones + proximity + recency)": "net",
    "lnc.ltc only": "lnc",
    "BM25": "bm25",
}

# How each kind of match is coloured in snippets and chips.
MATCH_COLOURS = {"exact": "#c8ecd4", "phonetic": "#cfe0ff", "xling": "#ffe0b8"}
MATCH_LABELS = {"exact": "exact", "phonetic": "phonetic", "xling": "translated"}

SENTENCE_END = regex.compile(r"(?<=[।.!?])\s+")


@st.cache_resource
def load_index(mode):
    # Swap this for the real index once it's ready: Index.load(mode).
    return SampleIndex.load(mode)


def run_ranker(ranker, query, index, k, doc_filter):
    if ranker == "net":
        return rank(query, index, k=k, doc_filter=doc_filter)
    if ranker == "lnc":
        return search(query, index, k=k, doc_filter=doc_filter)
    return search_bm25(query, index, k=k, doc_filter=doc_filter)


def term_sources(query):
    """Map each expanded term to how it matched: exact, phonetic or xling."""
    sources = {}
    for token in query["tokens"]:
        for term, _weight, source in token["expansions"]:
            sources.setdefault(term, source)
    return sources


def highlight(text, sources):
    """Wrap matched words in coloured marks. Escapes everything else."""
    out = []
    for piece in regex.split(r"([\p{L}\p{M}\p{Nd}]+)", text):
        source = sources.get(piece.lower())
        if source:
            out.append(
                f'<mark style="background:{MATCH_COLOURS[source]};padding:0 2px;border-radius:3px;color:#1a1a1a">'
                f"{html.escape(piece)}</mark>"
            )
        else:
            out.append(html.escape(piece))
    return "".join(out)


def snippet(body, sources, max_words=28):
    """The first sentence that contains a matched word, else the opening words."""
    sentences = SENTENCE_END.split(body)
    for sentence in sentences:
        if any(tok in sources for tok in tokenize(sentence)):
            return sentence
    words = body.split()
    return " ".join(words[:max_words]) + (" …" if len(words) > max_words else "")


def match_chips(matched_terms, sources):
    chips = []
    for term in matched_terms:
        source = sources.get(term, "exact")
        chips.append(
            f'<span style="background:{MATCH_COLOURS[source]};padding:1px 6px;border-radius:10px;color:#1a1a1a;'
            f'font-size:0.8em;margin-right:4px">{html.escape(term)} · {MATCH_LABELS[source]}</span>'
        )
    return "".join(chips)


def show_result(rank_no, doc_id, score, explain, index, sources, only_here):
    article = index.articles.get(doc_id, {"headline": doc_id, "body": ""})
    meta = index.meta[doc_id]
    terms = explain.get("terms", explain)

    badge = (
        ' <span style="background:#fde68a;color:#1a1a1a;padding:1px 6px;border-radius:10px;font-size:0.75em">only here</span>'
        if only_here else ""
    )
    st.markdown(f"**{rank_no}. {highlight(article['headline'], sources)}**{badge}", unsafe_allow_html=True)
    date = (meta.get("date") or "")[:10]
    place = meta.get("city") or meta.get("state") or ""
    details = " · ".join(x for x in (meta.get("source"), meta.get("section"), place, date) if x)
    st.caption(f"{details} · score {score:.3f}")
    st.markdown(highlight(snippet(article["body"], sources), sources), unsafe_allow_html=True)
    st.markdown(match_chips(list(terms), sources), unsafe_allow_html=True)

    with st.expander("Why this score"):
        if "cosine" in explain:
            st.write(
                {
                    "cosine": round(explain["cosine"], 4),
                    "zone": round(explain["zone"], 4),
                    "proximity": round(explain["proximity"], 4),
                    "recency g(d)": round(explain["recency"], 4),
                    "net": round(explain["net"], 4),
                }
            )
        st.write({term: round(v, 4) for term, v in terms.items()})


def main():
    st.set_page_config(page_title="Dhvani", layout="wide")
    st.title("Dhvani")
    st.caption("Hindi news search. Type in Hindi, Hinglish or English.")

    base_index = load_index("none")

    with st.sidebar:
        st.header("Ranking")
        ranker = RANKERS[st.selectbox("Ranker", list(RANKERS))]
        k = st.slider("Results per column", 3, 20, 10)

        st.header("Filters")
        sources = st.multiselect("Source", field_values(base_index, "source"))
        sections = st.multiselect("Section", field_values(base_index, "section"))
        states = st.multiselect("State", field_values(base_index, "state"))
        use_dates = st.checkbox("Filter by date")
        date_from = date_to = None
        if use_dates:
            date_from = st.date_input("From", key="date_from")
            date_to = st.date_input("To", key="date_to")

    raw = st.text_input("Search", value="दिल्ली बारिश", placeholder="कल का मौसम / kal ka mausam / weather tomorrow")
    if not raw.strip():
        st.info("Type a query to search.")
        return

    query = exact_query(raw)
    sources_map = term_sources(query)

    results = {}
    for mode, _label in MODES:
        index = load_index(mode)
        doc_filter = make_filter(index, sources, sections, states, date_from, date_to)
        results[mode] = run_ranker(ranker, query, index, k, doc_filter)

    if isinstance(load_index("none"), SampleIndex):
        st.info("Running on the 20-article sample index. The three columns will differ once the stemmed indexes are plugged in.")

    ids = {mode: {doc_id for doc_id, _, _ in res} for mode, res in results.items()}
    columns = st.columns(len(MODES))
    for col, (mode, label) in zip(columns, MODES):
        with col:
            st.subheader(label)
            if not results[mode]:
                st.write("No results.")
            others = set().union(*(ids[m] for m in ids if m != mode))
            for i, (doc_id, score, explain) in enumerate(results[mode], start=1):
                show_result(i, doc_id, score, explain, load_index(mode), sources_map, doc_id not in others)


if __name__ == "__main__":
    main()
