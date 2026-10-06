from index.positional import Index


def and_search(idx: Index, terms: list[str], zone: str = "body") -> list[str]:
    """
    Return documents containing all supplied terms.

    Results are returned in sorted document ID order.
    """

    if not terms:
        return []

    posting_lists = []

    for term in terms:
        postings = idx.postings_for(term, zone)

        if not postings:
            return []

        doc_ids = {doc_id for doc_id, _, _ in postings}
        posting_lists.append(doc_ids)

    result = posting_lists[0]

    for doc_ids in posting_lists[1:]:
        result &= doc_ids

    return sorted(result)


def phrase_search(
    idx: Index,
    terms: list[str],
    zone: str = "body",
) -> list[str]:
    """
    Return documents where all terms occur consecutively
    in the supplied order.

    Example:

        phrase_search(idx, ["बारिश", "हुई"])

    matches:

        "आज बारिश हुई"

    but not:

        "बारिश आज हुई"
    """

    if not terms:
        return []

    if len(terms) == 1:
        return sorted(
            doc_id
            for doc_id, _, _ in idx.postings_for(terms[0], zone)
        )

    # Retrieve postings for every term.
    postings_by_term = []

    for term in terms:
        postings = idx.postings_for(term, zone)

        if not postings:
            return []

        postings_by_term.append(
            {
                doc_id: positions
                for doc_id, _, positions in postings
            }
        )

    # Only documents containing every term can match.
    candidate_docs = set(postings_by_term[0])

    for postings in postings_by_term[1:]:
        candidate_docs &= set(postings)

    matches = []

    for doc_id in candidate_docs:
        first_positions = postings_by_term[0][doc_id]

        for start_position in first_positions:
            matches_phrase = True

            for offset, postings in enumerate(postings_by_term[1:], start=1):
                if start_position + offset not in postings[doc_id]:
                    matches_phrase = False
                    break

            if matches_phrase:
                matches.append(doc_id)
                break

    return sorted(matches)