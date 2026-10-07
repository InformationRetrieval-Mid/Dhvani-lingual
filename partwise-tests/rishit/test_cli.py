import importlib.util
from pathlib import Path

CLI_PATH = Path(__file__).resolve().parents[2] / "app" / "cli.py"
spec = importlib.util.spec_from_file_location("dhvani_cli", CLI_PATH)
cli = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cli)


def test_plain_search_lists_results(capsys):
    text = cli.run(["मौसम", "--ranker", "lnc", "--k", "3"])
    assert "Results" in text
    assert "1. " in text and "nbt_2001" in text
    assert "Query vector" not in text  # no explanation unless asked


def test_explain_shows_every_stage():
    text = cli.run(["दिल्ली बारिश", "--explain", "--k", "2"])
    for section in ("1. Query object", "2. Query vector", "3. Postings touched",
                    "4. Candidates and top K", "5. Results"):
        assert section in text
    assert "idf = log10(N/df)" in text
    assert "pos=[" in text            # positions from the postings
    assert "= net score" in text      # full breakdown for the net ranker


def test_explain_bm25_shows_bm25_idf():
    text = cli.run(["कोहली शतक", "--ranker", "bm25", "--explain", "--k", "2"])
    assert "k1 = 1.2" in text and "b = 0.75" in text
    assert "BM25 contribution" in text


def test_unknown_word_is_marked():
    text = cli.run(["xyz", "--explain"])
    assert "dropped, not in index" in text
    assert "No matches." in text


def test_kal_query_shows_its_direction():
    text = cli.run(["कल बारिश", "--k", "2"])
    assert "[kal: tomorrow]" in text


def test_kal_explain_has_its_own_step():
    text = cli.run(["कल बारिश", "--k", "1", "--explain"])
    assert "4c. Date-aware kal" in text
    assert "x kal boost (tomorrow)" in text


def test_no_kal_turns_it_off():
    text = cli.run(["कल बारिश", "--k", "2", "--no-kal"])
    assert "kal:" not in text
