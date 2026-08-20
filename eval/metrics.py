import math


def reciprocal_rank(ranked_results, query_documents):
    docs_by_source_file = {doc["source_file"]: doc for doc in query_documents} # lets us look up a result's judgement by source_file instead of scanning the list each time
    for rank, result in enumerate(ranked_results, start=1): # start=1 to prevent division by zero, counter is now 1-indexed
        source_file = result["document"]["source_file"]
        doc = docs_by_source_file.get(source_file) # None if this result isn't judged for this query (unjudged = treated as non-relevant, not an error)
        if doc and doc["relevance"] >= 2:
            return 1 / rank # first qualifying result found; RR is 1 over its rank
    return 0.0 # no result met the relevance threshold


def precision_at_k(ranked_results, query_documents, k):
    docs_by_source_file = {doc["source_file"]: doc for doc in query_documents}
    top_k = ranked_results[:k] # only the first k results count toward this metric
    relevant_count = 0
    for result in top_k:
        doc = docs_by_source_file.get(result["document"]["source_file"]) # None if unjudged (treated as non-relevant)
        if doc and doc["relevance"] >= 2:
            relevant_count += 1
    return relevant_count / k # dividing by k (not len(top_k)) so a short result list is penalized, not skipped


def ndcg_at_k(ranked_results, query_documents, k):
    docs_by_source_file = {doc["source_file"]: doc for doc in query_documents}
    gains = {0: 0, 1: 1, 2: 3, 3: 7} # exponential gain: 2^relevance - 1

    def discounted_gain(relevance, rank):
        return gains[relevance] / math.log2(rank + 1) # rank 1 -> log2(2) = 1, no discount; grows for lower ranks

    dcg = 0
    for rank, result in enumerate(ranked_results[:k], start=1):
        doc = docs_by_source_file.get(result["document"]["source_file"])
        relevance = doc["relevance"] if doc else 0 # unjudged results contribute no gain
        dcg += discounted_gain(relevance, rank)

    ideal_order = sorted(query_documents, key=lambda doc: doc["relevance"], reverse=True) # idcg_source: judged_pool - ideal ranking is just the judged docs sorted by relevance
    idcg = sum(discounted_gain(doc["relevance"], rank) for rank, doc in enumerate(ideal_order[:k], start=1))

    if idcg == 0: # no relevant docs judged for this query at all - avoid dividing by zero
        return 0.0
    return dcg / idcg
