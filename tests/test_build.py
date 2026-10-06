import json

import pytest

from index.build import build_index, build_indexes, iter_articles


def write_jsonl(path, articles):
    with path.open("w", encoding="utf-8") as file:
        for article in articles:
            file.write(json.dumps(article, ensure_ascii=False) + "\n")


def sample_articles():
    return [
        {
            "doc_id": "jagran_001",
            "url": "https://example.com/1",
            "source": "jagran",
            "section": "weather",
            "state": "uttar-pradesh",
            "city": "lucknow",
            "date": "2026-10-06T13:21:43+05:30",
            "headline": "लखनऊ में भारी बारिश",
            "body": "आज लखनऊ में भारी बारिश हुई।",
            "keywords": ["मौसम", "बारिश"],
            "agency_flag": False,
            "content_hash": "abc123",
            "dup_of": None,
            "links": [],
        },
        {
            "doc_id": "jagran_002",
            "url": "https://example.com/2",
            "source": "jagran",
            "section": "national",
            "state": "delhi",
            "city": "delhi",
            "date": "2026-10-06T14:00:00+05:30",
            "headline": "दिल्ली में मौसम साफ",
            "body": "दिल्ली में आज मौसम साफ रहा।",
            "keywords": ["मौसम"],
            "agency_flag": False,
            "content_hash": "def456",
            "dup_of": None,
            "links": ["jagran_001"],
        },
    ]


def test_iter_articles_reads_jsonl(tmp_path):
    path = tmp_path / "news.jsonl"
    articles = sample_articles()

    write_jsonl(path, articles)

    result = list(iter_articles(path))

    assert result == articles


def test_iter_articles_ignores_blank_lines(tmp_path):
    path = tmp_path / "news.jsonl"

    article = sample_articles()[0]

    with path.open("w", encoding="utf-8") as file:
        file.write("\n")
        file.write(json.dumps(article, ensure_ascii=False))
        file.write("\n\n")

    result = list(iter_articles(path))

    assert result == [article]


def test_iter_articles_rejects_invalid_json(tmp_path):
    path = tmp_path / "news.jsonl"

    path.write_text(
        '{"doc_id": "good", "headline": "अच्छी खबर", "body": "समाचार"}\n'
        '{"doc_id": "bad",\n',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Line 2: invalid JSON"):
        list(iter_articles(path))


def test_iter_articles_rejects_missing_required_field(tmp_path):
    path = tmp_path / "news.jsonl"

    article = sample_articles()[0]
    del article["headline"]

    write_jsonl(path, [article])

    with pytest.raises(
        ValueError,
        match="Line 1: missing required field 'headline'",
    ):
        list(iter_articles(path))


def test_iter_articles_rejects_non_string_headline(tmp_path):
    path = tmp_path / "news.jsonl"

    article = sample_articles()[0]
    article["headline"] = 123

    write_jsonl(path, [article])

    with pytest.raises(
        ValueError,
        match="Line 1: 'headline' must be a string",
    ):
        list(iter_articles(path))


def test_build_index_none_mode(tmp_path):
    input_path = tmp_path / "news.jsonl"
    output_path = tmp_path / "indexes" / "none.pkl"

    write_jsonl(input_path, sample_articles())

    index = build_index(
        input_path=input_path,
        mode="none",
        output_path=output_path,
    )

    assert index.mode == "none"
    assert index.N == 2
    assert output_path.exists()

    assert "लखनऊ" in index.vocab
    assert "बारिश" in index.vocab

    postings = index.postings("बारिश", "body")

    assert len(postings) == 1
    assert postings[0][0] == "jagran_001"


def test_build_index_light_mode(tmp_path):
    input_path = tmp_path / "news.jsonl"
    output_path = tmp_path / "indexes" / "light.pkl"

    write_jsonl(input_path, sample_articles())

    index = build_index(
        input_path=input_path,
        mode="light",
        output_path=output_path,
    )

    assert index.mode == "light"
    assert index.N == 2
    assert output_path.exists()


def test_build_index_preserves_metadata(tmp_path):
    input_path = tmp_path / "news.jsonl"
    output_path = tmp_path / "none.pkl"

    write_jsonl(input_path, sample_articles())

    index = build_index(
        input_path=input_path,
        mode="none",
        output_path=output_path,
    )

    metadata = index.meta["jagran_001"]

    assert metadata["source"] == "jagran"
    assert metadata["date"] == "2026-10-06T13:21:43+05:30"
    assert metadata["state"] == "uttar-pradesh"
    assert metadata["section"] == "weather"
    assert metadata["dup_of"] is None


def test_build_indexes_creates_both_indexes(tmp_path, monkeypatch):
    input_path = tmp_path / "news.jsonl"
    write_jsonl(input_path, sample_articles())

    monkeypatch.setattr(
        "index.positional.Index.INDEX_DIR",
        tmp_path / "indexes",
    )

    indexes = build_indexes(input_path)

    assert set(indexes.keys()) == {"none", "light"}

    assert indexes["none"].mode == "none"
    assert indexes["light"].mode == "light"

    assert indexes["none"].N == 2
    assert indexes["light"].N == 2

    assert (tmp_path / "indexes" / "none.pkl").exists()
    assert (tmp_path / "indexes" / "light.pkl").exists()


def test_build_index_rejects_unsupported_mode(tmp_path):
    input_path = tmp_path / "news.jsonl"
    write_jsonl(input_path, sample_articles())

    with pytest.raises(ValueError, match="Unsupported index mode"):
        build_index(
            input_path=input_path,
            mode="aggr",
        )