import math

from index.positional import Index
from index.scoring import idf, idf_table


def build_test_index():
    index = Index("none")

    index.add_document(
        "doc1",
        "दिल्ली बारिश",
        "दिल्ली में बारिश हुई",
        {},
    )

    index.add_document(
        "doc2",
        "दिल्ली मौसम",
        "दिल्ली में आज मौसम साफ है",
        {},
    )

    index.add_document(
        "doc3",
        "बारिश खबर",
        "मुंबई में बारिश हुई",
        {},
    )

    return index


def test_idf_for_common_term():
    index = build_test_index()

    # "दिल्ली" occurs in 2 of 3 documents.
    expected = math.log(3 / 2)

    assert math.isclose(
        idf(index, "दिल्ली"),
        expected,
        rel_tol=1e-9,
    )


def test_idf_for_term_in_every_document():
    index = build_test_index()

    # "में" occurs in all three documents.
    expected = math.log(3 / 3)

    assert math.isclose(
        idf(index, "में"),
        expected,
        rel_tol=1e-9,
    )


def test_idf_for_missing_term():
    index = build_test_index()

    assert idf(index, "अस्तित्वहीन") == 0.0


def test_idf_table():
    index = build_test_index()

    result = idf_table(
        index,
        ["दिल्ली", "बारिश", "मौसम"],
    )

    assert set(result.keys()) == {
        "दिल्ली",
        "बारिश",
        "मौसम",
    }

    assert result["दिल्ली"] > 0
    assert result["बारिश"] > 0
    assert result["मौसम"] > 0


def test_rare_terms_have_higher_idf():
    index = build_test_index()

    # "मौसम" occurs once, while "दिल्ली" occurs twice.
    assert idf(index, "मौसम") > idf(index, "दिल्ली")