import json
from pathlib import Path

import requests

from metrics import reciprocal_rank, precision_at_k, ndcg_at_k


BENCHMARK_PATH = Path(__file__).parent / "benchmark.json"
BASE_URL = "http://localhost:8000"


def load_benchmark():
    with open(BENCHMARK_PATH, "r") as file:
        return json.load(file) # loading the JSON file as a dictionary


def main():
    benchmark = load_benchmark()
    k_values = benchmark["evaluation_config"]["k_values"]
    reciprocal_ranks = []
    precisions = {k: [] for k in k_values} # k -> list of that query's precision@k, one entry per query
    ndcgs = {k: [] for k in k_values} # k -> list of that query's ndcg@k, one entry per query
    for query in benchmark["queries"]:
        response = requests.get(f"{BASE_URL}/search", params={"q": query["query"]}) # params represents the query parameters that should be attached to the URL of the GET request
        ranked_results = response.json() # deserializes JSON to python; we get an array of {"document" : x, "score" : y} dicts
        rr = reciprocal_rank(ranked_results, query["documents"])
        reciprocal_ranks.append(rr)
        print(f"  {rr:.4f}  {query['query']}")
        for k in k_values:
            precisions[k].append(precision_at_k(ranked_results, query["documents"], k))
            ndcgs[k].append(ndcg_at_k(ranked_results, query["documents"], k))

    mrr = sum(reciprocal_ranks) / len(reciprocal_ranks)
    print(f"\nMRR: {mrr:.4f}")
    for k in k_values:
        print(f"Precision@{k}: {sum(precisions[k]) / len(precisions[k]):.4f}")
    for k in k_values:
        print(f"NDCG@{k}: {sum(ndcgs[k]) / len(ndcgs[k]):.4f}")


if __name__ == "__main__":
    main()