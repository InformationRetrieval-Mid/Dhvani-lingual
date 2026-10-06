"""Dhvani search app.

Run from the repo root:
    streamlit run app/streamlit_app.py

Every query runs against three indexes side by side: no stemming, stemming,
and auto (stem a word only when it helps). Until the real indexes are ready
all three columns use the sample index, so they'll look the same.
"""

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dhvani.rank.bm25 import search_bm25  # noqa: E402
from dhvani.rank.query_stub import exact_query  # noqa: E402
from dhvani.rank.sample_index import SampleIndex  # noqa: E402
from dhvani.rank.scoring import rank  # noqa: E402
from dhvani.rank.vsm import search  # noqa: E402

MODES = [("none", "No stemming"), ("light", "Stemming"), ("auto", "Auto")]

RANKERS = {
    "Net score (lnc.ltc + zones + proximity + recency)": "net",
    "lnc.ltc only": "lnc",
    "BM25": "bm25",
}


@st.cache_resource
def load_index(mode):
    # Swap this for the real index once it's ready: Index.load(mode).
    return SampleIndex.load(mode)


def run_ranker(ranker, query, index, k):
    if ranker == "net":
        return rank(query, index, k=k)
    if ranker == "lnc":
        return search(query, index, k=k)
    return search_bm25(query, index, k=k)


def show_result(rank_no, doc_id, score, index):
    article = index.articles.get(doc_id, {"headline": doc_id, "body": ""})
    meta = index.meta[doc_id]
    st.markdown(f"**{rank_no}. {article['headline']}**")
    date = (meta.get("date") or "")[:10]
    place = meta.get("city") or meta.get("state") or ""
    details = " · ".join(x for x in (meta.get("source"), meta.get("section"), place, date) if x)
    st.caption(f"{details} · score {score:.3f}")


def main():
    st.set_page_config(page_title="Dhvani", layout="wide")
    st.title("Dhvani")
    st.caption("Hindi news search. Type in Hindi, Hinglish or English.")

    with st.sidebar:
        st.header("Ranking")
        ranker = RANKERS[st.selectbox("Ranker", list(RANKERS))]
        k = st.slider("Results per column", 3, 20, 10)

    raw = st.text_input("Search", value="दिल्ली बारिश", placeholder="कल का मौसम / kal ka mausam / weather tomorrow")
    if not raw.strip():
        st.info("Type a query to search.")
        return

    query = exact_query(raw)

    if isinstance(load_index("none"), SampleIndex):
        st.info("Running on the 20-article sample index. The three columns will differ once the stemmed indexes are plugged in.")

    columns = st.columns(len(MODES))
    for col, (mode, label) in zip(columns, MODES):
        index = load_index(mode)
        results = run_ranker(ranker, query, index, k)
        with col:
            st.subheader(label)
            if not results:
                st.write("No results.")
            for i, (doc_id, score, _explain) in enumerate(results, start=1):
                show_result(i, doc_id, score, index)


if __name__ == "__main__":
    main()
