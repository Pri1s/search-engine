def reciprocal_rank(ranked_results, query_documents):
    docs_by_source_file = {doc["source_file"]: doc for doc in query_documents} # lets us look up a result's judgement by source_file instead of scanning the list each time
    for rank, result in enumerate(ranked_results, start=1): # start=1 to prevent division by zero, counter is now 1-indexed
        source_file = result["document"]["source_file"]
        doc = docs_by_source_file.get(source_file) # None if this result isn't judged for this query (unjudged = treated as non-relevant, not an error)
        if doc and doc["relevance"] >= 2:
            return 1 / rank # first qualifying result found; RR is 1 over its rank
    return 0.0 # no result met the relevance threshold
