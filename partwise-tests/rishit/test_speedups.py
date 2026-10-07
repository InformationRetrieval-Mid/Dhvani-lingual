from dhvani.rank.query_stub import exact_query
from dhvani.rank.sample_index import SampleIndex
from dhvani.rank.speedups import (
    default_min_match,
    high_idf_terms,
    overlap_at_k,
    search_index_elimination,
    soft_and_candidates,
)
from dhvani.rank.vsm import query_vector, search


# --- index elimination -------------------------------------------------------

def test_low_idf_words_are_dropped():
    idx = SampleIndex.load()
    qvec = query_vector(exact_query("बारिश में अलर्ट"), idx)
    kept, idf = high_idf_terms(qvec, idx, min_idf=0.3)
    # में is in 15 of 20 articles (idf 0.125), so it's skipped.
    assert "में" not in kept
    assert {"बारिश", "अलर्ट"} <= set(kept)


def test_rarest_term_is_kept_even_if_all_are_common():
    idx = SampleIndex.load()
    qvec = query_vector(exact_query("में ने"), idx)
    kept, idf = high_idf_terms(qvec, idx, min_idf=5.0)
    assert kept == [max(qvec, key=lambda t: idf[t])]


def test_soft_and_needs_enough_terms():
    idx = SampleIndex.load()
    both = soft_and_candidates(idx, ["दिल्ली", "बारिश"], 2)
    either = soft_and_candidates(idx, ["दिल्ली", "बारिश"], 1)
    assert both < either
    assert "jagran_1001" in both and "amarujala_3001" not in both


def test_min_match_follows_the_lecture_example():
    assert default_min_match(4) == 3
    assert default_min_match(2) == 1
    assert default_min_match(1) == 1


def test_scores_fewer_articles_than_full_search():
    idx = SampleIndex.load()
    results, stats = search_index_elimination(exact_query("दिल्ली में बारिश का अलर्ट"), idx, k=3)
    assert stats["scored"] < stats["full_candidates"]
    assert set(stats["terms_dropped"]) >= {"में"}
    assert results[0][0] == "jagran_1001"


def test_top_k_stays_close_to_exact():
    idx = SampleIndex.load()
    q = exact_query("दिल्ली में बारिश का अलर्ट")
    fast, _ = search_index_elimination(q, idx, k=3)
    assert overlap_at_k(fast, search(q, idx, k=3), k=3) >= 2 / 3


def test_relaxes_when_too_strict():
    idx = SampleIndex.load()
    # Nothing contains both कोहली and बिहार, but the search still returns k.
    results, stats = search_index_elimination(exact_query("कोहली बिहार"), idx, k=2, min_match=2)
    assert len(results) == 2
    assert stats["min_match"] == 1


def test_unknown_words_give_nothing():
    results, stats = search_index_elimination(exact_query("xyzabc"), SampleIndex.load())
    assert results == [] and stats["scored"] == 0


def test_overlap_at_k():
    a = [("x", 1, {}), ("y", 1, {}), ("z", 1, {})]
    b = [("x", 1, {}), ("q", 1, {}), ("z", 1, {})]
    assert overlap_at_k(a, b, k=3) == 2 / 3
    assert overlap_at_k(a, [], k=3) == 1.0
