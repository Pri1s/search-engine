import json
from datetime import datetime
from pathlib import Path

import requests

from metrics import reciprocal_rank, precision_at_k, ndcg_at_k


BENCHMARK_PATH = Path(__file__).parent / "benchmark.json"
RUNS_DIR = Path(__file__).parent / "runs"
BASE_URL = "http://localhost:8000"


def load_benchmark():
    with open(BENCHMARK_PATH, "r") as file:
        return json.load(file) # loading the JSON file as a dictionary


def main():
    benchmark = load_benchmark()
    config = benchmark["evaluation_config"]
    k_values = config["k_values"]
    reciprocal_ranks = []
    precisions = {k: [] for k in k_values} # k -> list of that query's precision@k, one entry per query
    ndcgs = {k: [] for k in k_values} # k -> list of that query's ndcg@k, one entry per query
    query_results = []
    for query in benchmark["queries"]:
        response = requests.get(f"{BASE_URL}/search", params={"q": query["query"]}) # params represents the query parameters that should be attached to the URL of the GET request
        ranked_results = response.json() # deserializes JSON to python; we get an array of {"document" : x, "score" : y} dicts
        rr = reciprocal_rank(ranked_results, query["documents"])
        reciprocal_ranks.append(rr)
        query_precision_at_k = {}
        query_ndcg_at_k = {}
        for k in k_values:
            p = precision_at_k(ranked_results, query["documents"], k)
            n = ndcg_at_k(ranked_results, query["documents"], k)
            precisions[k].append(p)
            ndcgs[k].append(n)
            query_precision_at_k[str(k)] = round(p, 3)
            query_ndcg_at_k[str(k)] = round(n, 3)
        query_results.append({
            "query_id": query["query_id"],
            "query": query["query"],
            "reciprocal_rank": round(rr, 3),
            "precision_at_k": query_precision_at_k,
            "ndcg_at_k": query_ndcg_at_k,
        })

    mrr = sum(reciprocal_ranks) / len(reciprocal_ranks)
    overall_precision_at_k = {str(k): round(sum(precisions[k]) / len(precisions[k]), 3) for k in k_values}
    overall_ndcg_at_k = {str(k): round(sum(ndcgs[k]) / len(ndcgs[k]), 3) for k in k_values}

    now = datetime.now().astimezone()
    run_id = now.strftime("%Y-%m-%dT%H-%M-%S")
    run = {
        "run_id": run_id,
        "benchmark_version": benchmark["benchmark_version"],
        "timestamp": now.isoformat(),
        "config": config,
        "overall_metrics": {
            "mrr": round(mrr, 3),
            "precision_at_k": overall_precision_at_k,
            "ndcg_at_k": overall_ndcg_at_k,
        },
        "queries": query_results,
    }

    RUNS_DIR.mkdir(exist_ok=True)
    run_path = RUNS_DIR / f"{run_id}.json"
    with open(run_path, "w") as file:
        json.dump(run, file, indent=2)


if __name__ == "__main__":
    main()