import json

import pytest

from index.build import build_index, iter_articles


def sample_articles():
    return [
        {
            "doc_id": "doc1",
            "url": "https://example.com/doc1",
            "source": "jagran",
            "section": "weather",
            "state": "uttar-pradesh",
            "city": "lucknow",
            "date": "2026-10-06T13:21:43+05:30",
            "headline": "लखनऊ में बारिश",
            "body": "लखनऊ में आज भारी बारिश हुई।",
            "keywords": ["बारिश"],
            "agency_flag": False,
            "content_hash": "hash1",
            "dup_of": None,
            "links": [],
        },
        {
            "doc_id": "doc2",
            "url": "https://example.com/doc2",
            "source": "pti",
            "section": "national",
            "state": "delhi",
            "city": "new-delhi",
            "date": "2026-10-06T14:00:00+05:30",
            "headline": "दिल्ली में मौसम",
            "body": "दिल्ली में मौसम साफ रहा।",
            "keywords": ["मौसम"],
            "agency_flag": True,
            "content_hash": "hash2",
            "dup_of": None,
            "links": ["https://example.com/related"],
        },
    ]


def write_jsonl(path, articles):
    with path.open("w", encoding="utf-8") as file:
        for article in articles:
            file.write(
                json.dumps(
                    article,
                    ensure_ascii=False,
                )
                + "\n"
            )


def test_iter_articles_reads_jsonl(tmp_path):
    input_path = tmp_path / "news.jsonl"
    articles = sample_articles()

    write_jsonl(input_path, articles)

    result = list(iter_articles(input_path))

    assert result == articles


def test_iter_articles_skips_blank_lines(tmp_path):
    input_path = tmp_path / "news.jsonl"
    articles = sample_articles()

    with input_path.open("w", encoding="utf-8") as file:
        file.write("\n")
        file.write(
            json.dumps(
                articles[0],
                ensure_ascii=False,
            )
            + "\n"
        )
        file.write("\n")

    result = list(iter_articles(input_path))

    assert result == [articles[0]]


def test_iter_articles_missing_file(tmp_path):
    input_path = tmp_path / "missing.jsonl"

    with pytest.raises(FileNotFoundError):
        list(iter_articles(input_path))


def test_iter_articles_invalid_json(tmp_path):
    input_path = tmp_path / "news.jsonl"

    valid_article = sample_articles()[0]

    with input_path.open("w", encoding="utf-8") as file:
        file.write(
            json.dumps(
                valid_article,
                ensure_ascii=False,
            )
            + "\n"
        )

        file.write(
            '{"invalid json"\n'
        )

    with pytest.raises(
        ValueError,
        match="invalid JSON",
    ):
        list(iter_articles(input_path))


def test_iter_articles_missing_required_field(tmp_path):
    input_path = tmp_path / "news.jsonl"

    article = sample_articles()[0]
    del article["headline"]

    write_jsonl(input_path, [article])

    with pytest.raises(
        ValueError,
        match="missing required field 'headline'",
    ):
        list(iter_articles(input_path))


def test_iter_articles_invalid_doc_id(tmp_path):
    input_path = tmp_path / "news.jsonl"

    article = sample_articles()[0]
    article["doc_id"] = 123

    write_jsonl(input_path, [article])

    with pytest.raises(
        ValueError,
        match="'doc_id' must be a string",
    ):
        list(iter_articles(input_path))


def test_iter_articles_invalid_headline(tmp_path):
    input_path = tmp_path / "news.jsonl"

    article = sample_articles()[0]
    article["headline"] = None

    write_jsonl(input_path, [article])

    with pytest.raises(
        ValueError,
        match="'headline' must be a string",
    ):
        list(iter_articles(input_path))


def test_iter_articles_invalid_body(tmp_path):
    input_path = tmp_path / "news.jsonl"

    article = sample_articles()[0]
    article["body"] = None

    write_jsonl(input_path, [article])

    with pytest.raises(
        ValueError,
        match="'body' must be a string",
    ):
        list(iter_articles(input_path))


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
        "city": "lucknow",
        "section": "weather",
        "dup_of": None,
        "links": [],
    }

    assert index.meta["doc2"] == {
        "source": "pti",
        "date": "2026-10-06T14:00:00+05:30",
        "state": "delhi",
        "city": "new-delhi",
        "section": "national",
        "dup_of": None,
        "links": ["https://example.com/related"],
    }


def test_build_index_stores_document_count(tmp_path):
    input_path = tmp_path / "news.jsonl"

    write_jsonl(
        input_path,
        sample_articles(),
    )

    index = build_index(
        input_path,
        "none",
        output_path=tmp_path / "indexes" / "none.pkl",
    )

    assert index.N == 2


def test_build_index_stores_vocabulary(tmp_path):
    input_path = tmp_path / "news.jsonl"

    write_jsonl(
        input_path,
        sample_articles(),
    )

    index = build_index(
        input_path,
        "none",
        output_path=tmp_path / "indexes" / "none.pkl",
    )

    assert "लखनऊ" in index.vocab
    assert "बारिश" in index.vocab
    assert "मौसम" in index.vocab


def test_build_index_stores_document_text(tmp_path):
    input_path = tmp_path / "news.jsonl"

    articles = sample_articles()
    write_jsonl(input_path, articles)

    index = build_index(
        input_path,
        "none",
        output_path=tmp_path / "indexes" / "none.pkl",
    )

    assert index.text["doc1"]["headline"] == "लखनऊ में बारिश"

    assert (
        index.text["doc1"]["body"]
        == "लखनऊ में आज भारी बारिश हुई।"
    )


def test_build_index_calculates_doc_len(tmp_path):
    input_path = tmp_path / "news.jsonl"

    write_jsonl(
        input_path,
        sample_articles(),
    )

    index = build_index(
        input_path,
        "none",
        output_path=tmp_path / "indexes" / "none.pkl",
    )

    assert "doc1" in index.doc_len
    assert index.doc_len["doc1"] > 0

    assert "doc2" in index.doc_len
    assert index.doc_len["doc2"] > 0


def test_build_index_calculates_doc_norm(tmp_path):
    input_path = tmp_path / "news.jsonl"

    write_jsonl(
        input_path,
        sample_articles(),
    )

    index = build_index(
        input_path,
        "none",
        output_path=tmp_path / "indexes" / "none.pkl",
    )

    assert "doc1" in index.doc_norm
    assert index.doc_norm["doc1"] > 0

    assert "doc2" in index.doc_norm
    assert index.doc_norm["doc2"] > 0


def test_build_index_rejects_duplicate_documents(tmp_path):
    input_path = tmp_path / "news.jsonl"

    articles = sample_articles()
    articles.append(articles[0].copy())

    write_jsonl(input_path, articles)

    with pytest.raises(
        ValueError,
        match="Document already exists",
    ):
        build_index(
            input_path,
            "none",
            output_path=tmp_path / "indexes" / "none.pkl",
        )


def test_build_index_rejects_invalid_mode(tmp_path):
    input_path = tmp_path / "news.jsonl"

    write_jsonl(
        input_path,
        sample_articles(),
    )

    with pytest.raises(
        ValueError,
        match="Unsupported index mode",
    ):
        build_index(
            input_path,
            "invalid",
        )


def test_build_index_saves_index(tmp_path):
    input_path = tmp_path / "news.jsonl"
    output_path = tmp_path / "indexes" / "none.pkl"

    write_jsonl(
        input_path,
        sample_articles(),
    )

    index = build_index(
        input_path,
        "none",
        output_path=output_path,
    )

    assert output_path.exists()
    assert index.N == 2