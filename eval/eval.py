import json
from pathlib import Path

import requests

from metrics import reciprocal_rank


BENCHMARK_PATH = Path(__file__).parent / "benchmark.json"
BASE_URL = "http://localhost:8000"


def load_benchmark():
    with open(BENCHMARK_PATH, "r") as file:
        return json.load(file) # loading the JSON file as a dictionary


def main():
    benchmark = load_benchmark()
    reciprocal_ranks = []
    for query in benchmark["queries"]:
        response = requests.get(f"{BASE_URL}/search", params={"q": query["query"]}) # params represents the query parameters that should be attached to the URL of the GET request
        ranked_results = response.json() # deserializes JSON to python; we get an array of {"document" : x, "score" : y} dicts
        rr = reciprocal_rank(ranked_results, query["documents"])
        reciprocal_ranks.append(rr)
        print(f"  {rr:.4f}  {query['query']}")

    mrr = sum(reciprocal_ranks) / len(reciprocal_ranks)
    print(f"\nMRR: {mrr:.4f}")


if __name__ == "__main__":
    main()