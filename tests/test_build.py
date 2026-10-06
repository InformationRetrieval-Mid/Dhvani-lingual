import json

import pytest

from index.build import (
    build_index,
    build_indexes,
    iter_articles,
)


def sample_articles():
    return [
        {
            "doc_id": "doc1",
            "url": "https://example.com/1",
            "source": "jagran",
            "section": "weather",
            "state": "uttar-pradesh",
            "city": "lucknow",
            "date": "2026-10-06T13:21:43+05:30",
            "headline": "दिल्ली में बारिश",
            "body": "आज दिल्ली में तेज बारिश हुई",
            "keywords": ["बारिश", "मौसम"],
            "agency_flag": False,
            "content_hash": "hash1",
            "dup_of": None,
            "links": [],
        },
        {
            "doc_id": "doc2",
            "url": "https://example.com/2",
            "source": "aaj-tak",
            "section": "weather",
            "state": "delhi",
            "city": "delhi",
            "date": "2026-10-06T14:00:00+05:30",
            "headline": "दिल्ली मौसम अपडेट",
            "body": "दिल्ली में आज मौसम साफ रहेगा",
            "keywords": ["मौसम"],
            "agency_flag": False,
            "content_hash": "hash2",
            "dup_of": None,
            "links": [],
        },
    ]


def write_jsonl(path, articles):
    with path.open("w", encoding="utf-8") as file:
        for article in articles:
            file.write(json.dumps(article, ensure_ascii=False))
            file.write("\n")


def test_iter_articles_reads_jsonl(tmp_path):
    input_path = tmp_path / "news.jsonl"
    articles = sample_articles()

    write_jsonl(input_path, articles)

    result = list(iter_articles(input_path))

    assert result == articles


def test_iter_articles_ignores_blank_lines(tmp_path):
    input_path = tmp_path / "news.jsonl"
    articles = sample_articles()

    with input_path.open("w", encoding="utf-8") as file:
        file.write("\n")
        file.write(
            json.dumps(
                articles[0],
                ensure_ascii=False,
            )
        )
        file.write("\n\n")
        file.write(
            json.dumps(
                articles[1],
                ensure_ascii=False,
            )
        )
        file.write("\n")

    result = list(iter_articles(input_path))

    assert result == articles


def test_iter_articles_invalid_json(tmp_path):
    input_path = tmp_path / "news.jsonl"

    input_path.write_text(
        '{"doc_id": "doc1",\n',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="invalid JSON"):
        list(iter_articles(input_path))


def test_iter_articles_missing_required_field(tmp_path):
    input_path = tmp_path / "news.jsonl"

    article = {
        "doc_id": "doc1",
        "headline": "बारिश",
    }

    input_path.write_text(
        json.dumps(article, ensure_ascii=False),
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="missing required field 'body'",
    ):
        list(iter_articles(input_path))


def test_iter_articles_non_string_headline(tmp_path):
    input_path = tmp_path / "news.jsonl"

    article = sample_articles()[0]
    article["headline"] = 123

    write_jsonl(input_path, [article])

    with pytest.raises(
        ValueError,
        match="'headline' must be a string",
    ):
        list(iter_articles(input_path))


def test_build_index_none(tmp_path, monkeypatch):
    input_path = tmp_path / "news.jsonl"
    write_jsonl(input_path, sample_articles())

    monkeypatch.setattr(
        "index.positional.Index.INDEX_DIR",
        tmp_path / "indexes",
    )

    index = build_index(input_path, "none")

    assert index.mode == "none"
    assert index.N == 2
    assert len(index.vocab) > 0


def test_build_index_light(tmp_path, monkeypatch):
    input_path = tmp_path / "news.jsonl"
    write_jsonl(input_path, sample_articles())

    monkeypatch.setattr(
        "index.positional.Index.INDEX_DIR",
        tmp_path / "indexes",
    )

    index = build_index(input_path, "light")

    assert index.mode == "light"
    assert index.N == 2
    assert len(index.vocab) > 0


def test_build_index_aggressive(tmp_path, monkeypatch):
    input_path = tmp_path / "news.jsonl"
    write_jsonl(input_path, sample_articles())

    monkeypatch.setattr(
        "index.positional.Index.INDEX_DIR",
        tmp_path / "indexes",
    )

    index = build_index(input_path, "aggr")

    assert index.mode == "aggr"
    assert index.N == 2
    assert len(index.vocab) > 0


def test_build_index_preserves_metadata(tmp_path, monkeypatch):
    input_path = tmp_path / "news.jsonl"
    articles = sample_articles()

    write_jsonl(input_path, articles)

    monkeypatch.setattr(
        "index.positional.Index.INDEX_DIR",
        tmp_path / "indexes",
    )

    index = build_index(input_path, "none")

    assert index.meta["doc1"] == {
        "source": "jagran",
        "date": "2026-10-06T13:21:43+05:30",
        "state": "uttar-pradesh",
        "section": "weather",
        "dup_of": None,
    }


def test_build_indexes_creates_all_indexes(tmp_path, monkeypatch):
    input_path = tmp_path / "news.jsonl"
    write_jsonl(input_path, sample_articles())

    monkeypatch.setattr(
        "index.positional.Index.INDEX_DIR",
        tmp_path / "indexes",
    )

    indexes = build_indexes(input_path)

    assert set(indexes.keys()) == {
        "none",
        "light",
        "aggr",
    }

    assert indexes["none"].mode == "none"
    assert indexes["light"].mode == "light"
    assert indexes["aggr"].mode == "aggr"

    assert indexes["none"].N == 2
    assert indexes["light"].N == 2
    assert indexes["aggr"].N == 2


def test_build_index_rejects_unsupported_mode(tmp_path):
    input_path = tmp_path / "news.jsonl"
    write_jsonl(input_path, sample_articles())

    with pytest.raises(
        ValueError,
        match="Unsupported index mode",
    ):
        build_index(input_path, "invalid")


def test_build_index_missing_file(tmp_path):
    input_path = tmp_path / "does_not_exist.jsonl"

    with pytest.raises(FileNotFoundError):
        build_index(input_path, "none")