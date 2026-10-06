"""Vector space scoring with the SMART lnc.ltc scheme (Lecture 6, Lecture 7).

Document side (lnc): weight = 1 + log10(tf), no idf, cosine-normalised.
Query side   (ltc): weight = (1 + log10(qtf)) * idf * expansion weight, cosine-normalised.
idf = log10(N / df).

Note the tf weight is 1 + log10(tf), not log10(1 + tf); Lecture 7 slide 2
corrects that bug from Lecture 6.

The top K documents are picked with a heap instead of sorting every score
(Lecture 7: selecting the K largest is much cheaper than a full sort).
"""

import heapq
import math
from collections import defaultdict

ZONES = ("headline", "body")


def log_tf(tf):
    return 1 + math.log10(tf) if tf > 0 else 0.0


def query_vector(query, index):
    """Turn a query object into normalised ltc weights: {term: weight}.

    A term that appears several times in the query (or comes from several
    expansions) adds up its expansion weights into its query tf.
    """
    qtf = defaultdict(float)
    for token in query["tokens"]:
        for term, weight, _source in token["expansions"]:
            qtf[term] += weight

    raw = {}
    for term, tf in qtf.items():
        df = index.df(term)
        if df == 0:
            continue  # term not in the collection, it can't match anything
        idf = math.log10(index.N / df)
        # tf can be fractional when it comes from weighted expansions; keep
        # weights below 1 as they are instead of letting log10 go negative.
        tf_weight = log_tf(tf) if tf >= 1 else tf
        raw[term] = tf_weight * idf

    norm = math.sqrt(sum(w * w for w in raw.values()))
    if norm == 0:
        return {}
    return {term: w / norm for term, w in raw.items()}


def search(query, index, k=10):
    """Rank documents for a query with lnc.ltc and return the top k.

    Returns [(doc_id, score, explain)], best first. explain maps each
    matching term to its contribution, which --explain prints later.
    """
    qvec = query_vector(query, index)

    # Term-at-a-time accumulation (Lecture 6 "computing cosine scores"),
    # only touching documents that contain at least one query term.
    scores = defaultdict(float)
    contributions = defaultdict(dict)
    for term, q_weight in qvec.items():
        doc_tf = defaultdict(int)
        for zone in ZONES:
            for doc_id, tf, _positions in index.postings(term, zone):
                doc_tf[doc_id] += tf
        for doc_id, tf in doc_tf.items():
            d_weight = log_tf(tf) / index.doc_norm[doc_id]
            part = q_weight * d_weight
            scores[doc_id] += part
            contributions[doc_id][term] = part

    top = heapq.nlargest(k, scores.items(), key=lambda item: (item[1], item[0]))
    return [(doc_id, score, contributions[doc_id]) for doc_id, score in top]
