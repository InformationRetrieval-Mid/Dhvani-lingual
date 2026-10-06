import math

from index.positional import Index


def idf(index: Index, term: str) -> float:
    """
    Calculate inverse document frequency for a term.

    IDF(t) = log(N / df(t))

    Returns 0.0 for terms that do not occur in the index.
    """
    df = index.df(term)

    if df == 0:
        return 0.0

    return math.log(index.N / df)


def idf_table(index: Index, terms):
    """
    Return a dictionary mapping each term to its IDF.
    """
    return {
        term: idf(index, term)
        for term in terms
    }