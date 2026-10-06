from index.positional import Index

from index.search import and_search, phrase_search


def build_test_index():
    idx = Index("none")

    idx.add_document(
        "doc1",
        "दिल्ली में बारिश",
        "आज दिल्ली में बारिश हुई",
        {},
    )

    idx.add_document(
        "doc2",
        "दिल्ली मौसम अपडेट",
        "दिल्ली में आज तेज बारिश हुई",
        {},
    )

    idx.add_document(
        "doc3",
        "बारिश की खबर",
        "मुंबई में बारिश हुई",
        {},
    )

    return idx


def test_and_search():
    idx = build_test_index()

    result = and_search(
        idx,
        ["दिल्ली", "बारिश"],
        "body",
    )

    assert result == ["doc1", "doc2"]


def test_and_search_returns_empty_when_term_missing():
    idx = build_test_index()

    result = and_search(
        idx,
        ["दिल्ली", "मुंबई"],
        "body",
    )

    assert result == []


def test_and_search_single_term():
    idx = build_test_index()

    result = and_search(
        idx,
        ["बारिश"],
        "body",
    )

    assert result == ["doc1", "doc2", "doc3"]


def test_phrase_search():
    idx = build_test_index()

    result = phrase_search(
        idx,
        ["बारिश", "हुई"],
        "body",
    )

    assert result == ["doc1", "doc2", "doc3"]


def test_phrase_search_respects_order():
    idx = build_test_index()

    result = phrase_search(
        idx,
        ["दिल्ली", "में", "बारिश"],
        "body",
    )

    # doc1 contains:
    # आज दिल्ली में बारिश हुई
    #
    # doc2 contains:
    # दिल्ली में आज तेज बारिश हुई
    #
    # Therefore only doc1 contains the exact phrase.
    assert result == ["doc1"]


def test_phrase_search_does_not_match_non_consecutive_terms():
    idx = build_test_index()

    result = phrase_search(
        idx,
        ["दिल्ली", "बारिश"],
        "body",
    )

    assert result == []


def test_phrase_search_respects_zone():
    idx = build_test_index()

    result = phrase_search(
        idx,
        ["दिल्ली", "में"],
        "headline",
    )

    # doc1 headline is:
    # दिल्ली में बारिश
    #
    # Therefore the phrase exists in the headline zone.
    assert result == ["doc1"]


def test_empty_search():
    idx = build_test_index()

    assert and_search(idx, []) == []
    assert phrase_search(idx, []) == []