from text.analyzer import analyze


SUPPORTED_MODES = {"none", "light", "aggr"}


def search_query(idx, query: str, mode: str = None, zone: str = "body"):
    """
    Search an Index using a raw text query.

    The query is analyzed using the requested mode and then all query
    terms are matched using Boolean AND search.

    Parameters
    ----------
    idx:
        An Index instance.

    query:
        Raw user query.

    mode:
        Analysis mode. If omitted, uses the mode of the supplied index.

    zone:
        "headline" or "body".

    Returns
    -------
    list[str]
        Matching document IDs.
    """

    if mode is None:
        mode = idx.mode

    if mode not in SUPPORTED_MODES:
        raise ValueError(f"Unsupported analysis mode: {mode}")

    if mode != idx.mode:
        raise ValueError(
            f"Query mode '{mode}' does not match index mode '{idx.mode}'"
        )

    if zone not in {"headline", "body"}:
        raise ValueError(
            f"Unsupported zone: {zone}"
        )

    analyzed = analyze(query, mode)

    terms = [term for term, _ in analyzed]

    if not terms:
        return []

    # Import here to avoid unnecessary coupling during module loading.
    from index.search import and_search

    return and_search(
        idx,
        terms,
        zone=zone,
    )


def search_both(idx_none, idx_light, query: str, zone: str = "body"):
    """
    Run the same raw query against both the no-stem and light indexes.

    Returns a dictionary suitable for comparing the two search modes.
    """

    return {
        "none": search_query(
            idx_none,
            query,
            mode="none",
            zone=zone,
        ),
        "light": search_query(
            idx_light,
            query,
            mode="light",
            zone=zone,
        ),
    }