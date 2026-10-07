from dhvani.query import match as M
from dhvani.query.editdist import learn_costs
from dhvani.query.kgram import KGramIndex

VOCAB = ["मौसम", "बारिश", "तापमान", "क्रिकेट", "चुनाव", "बाजार", "स्कूल"]

# Enough signal for the learned matcher to behave sensibly in the test.
TRAIN = [("mausam", "mosam")] * 5 + [("baarish", "barish")] * 5 + [("mausam", "mausam")] * 5


def _costs():
    return learn_costs(TRAIN, iterations=3)


def test_all_four_matchers_find_the_right_word():
    idx = KGramIndex(VOCAB, k=2)
    costs = _costs()
    for matcher in M.MATCHERS:
        top = M.rank("mosam", idx, matcher=matcher, costs=costs, k=3)
        assert top, f"{matcher} returned nothing"
        assert top[0][0] == "मौसम", f"{matcher} ranked {top[0][0]} first"


def test_weighted_variants_shape_and_weights():
    idx = KGramIndex(VOCAB, k=2)
    variants = M.weighted_variants("mosam", idx, _costs(), k=5)
    assert variants, "expected at least one variant"
    # Format-4 expansion entries: (term, weight, "phonetic").
    for term, weight, source in variants:
        assert isinstance(term, str)
        assert 0.0 <= weight <= 1.0
        assert source == "phonetic"
    assert abs(sum(w for _t, w, _s in variants) - 1.0) < 1e-9
    # The best match carries the largest weight.
    assert variants[0][0] == "मौसम"
    assert variants[0][1] == max(w for _t, w, _s in variants)


def test_iyer_reaches_ayyar_even_when_kgram_pool_misses_it():
    # Distractors out-compete अय्यर on k-gram overlap; with a small pool the
    # k-gram step alone would drop it. Phonetic-code candidates rescue it so the
    # matcher ranks अय्यर top instead of a wrong word like श्रेयस.
    vocab = ["अय्यर", "श्रेयस", "मेयर", "लेयर", "बायर", "सायर", "वीर", "तीर"]
    idx = KGramIndex(vocab, k=2)
    costs = learn_costs([("iyer", "ayyar")] * 3 + [("x", "x")] * 3, iterations=2)
    for matcher in ("dhvani", "learned", "levenshtein"):
        top = M.rank("iyer", idx, matcher=matcher, costs=costs, k=1, pool=3)
        assert top[0][0] == "अय्यर", f"{matcher} ranked {top[0][0]} first"


def test_unknown_matcher_raises():
    idx = KGramIndex(VOCAB, k=2)
    try:
        M.rank("mosam", idx, matcher="nope", costs=_costs())
    except ValueError:
        return
    raise AssertionError("expected ValueError for an unknown matcher")
