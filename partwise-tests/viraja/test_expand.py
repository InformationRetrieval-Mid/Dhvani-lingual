from dhvani.query.build import build_query
from dhvani.query.editdist import learn_costs
from dhvani.query.expand import expand_query
from dhvani.query.kgram import KGramIndex

VOCAB = ["मौसम", "बारिश", "तापमान", "क्रिकेट", "चुनाव", "बाजार"]
TRAIN = [("mausam", "mosam")] * 5 + [("baarish", "barish")] * 5 + [("mausam", "mausam")] * 5


def _index_and_costs():
    return KGramIndex(VOCAB, k=2), learn_costs(TRAIN, iterations=3)


def test_build_query_stays_exact_without_an_index():
    q = build_query("mosam")
    assert q["tokens"][0]["expansions"] == [("mosam", 1.0, "exact")]


def test_build_query_adds_phonetic_variants_with_index():
    index, costs = _index_and_costs()
    q = build_query("mosam", index=index, costs=costs)
    exps = q["tokens"][0]["expansions"]
    # Exact stays first; a phonetic मौसम is appended.
    assert exps[0] == ("mosam", 1.0, "exact")
    phonetic = [(t, s) for t, _w, s in exps if s == "phonetic"]
    assert ("मौसम", "phonetic") in phonetic


def test_expand_query_does_not_duplicate_terms():
    index, costs = _index_and_costs()
    q = build_query("barish", index=index, costs=costs)
    terms = [t for t, _w, _s in q["tokens"][0]["expansions"]]
    assert len(terms) == len(set(terms))


def test_expand_is_idempotent():
    index, costs = _index_and_costs()
    q = build_query("mosam", index=index, costs=costs)
    before = list(q["tokens"][0]["expansions"])
    expand_query(q, index, costs)  # running again adds nothing new
    assert q["tokens"][0]["expansions"] == before
