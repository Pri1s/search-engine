# Search Engine

A domain-specific (vertical) search engine, currently focused on basketball. A FastAPI backend backed by PostgreSQL, with document create/read endpoints, a JSON-based ingestion script, and a BM25-ranked search endpoint backed by an in-memory inverted index (separate title and body indexes, so title matches are boosted).

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [uv](https://docs.astral.sh/uv/) (Python package/dependency manager)

## Setup

1. **Start PostgreSQL via Docker**

   ```bash
   docker compose up -d
   ```

   This starts a Postgres 16 container listening on `localhost:5432`, with credentials matching `backend/.env`.

2. **Configure environment variables**

   `backend/.env` should contain:

   ```
   DATABASE_URL = "postgresql://searchengine:searchengine@localhost:5432/searchengine"
   ```

   (Already set up if you're using the default `docker-compose.yml` in this repo.)

3. **Install backend dependencies**

   ```bash
   cd backend
   uv sync
   ```

4. **Run the API server**

   ```bash
   uv run uvicorn main:app --reload
   ```

   The API will be available at [http://localhost:8000](http://localhost:8000), with interactive docs at [http://localhost:8000/docs](http://localhost:8000/docs).

## Ingesting documents

Sample documents live as JSON files in `data/documents/` (one file per document, with `title`, `url`, and `content` fields). To load them into the database:

```bash
cd backend
uv run ingest_documents.py
```

To fetch a fresh corpus of curated basketball Wikipedia articles into `data/documents/` (regenerates the sample documents used above):

```bash
uv run scripts/fetch_wikipedia_corpus.py
```

## Searching

The inverted index is built from the documents in the database at server startup. Query it via:

```bash
curl "http://localhost:8000/search?q=michael+jordan"
```

The response is a list of hits ordered by descending score, each wrapping the full document alongside its BM25 score:

```json
[
  { "document": { "id": 1, "title": "Michael Jordan", "url": "...", "content": "...", "created_at": "..." }, "score": 18.42 }
]
```

Results are ranked with BM25 (see [Search ranking](#search-ranking) below).

## Frontend

A minimal React (Vite) UI for searching, in `frontend/`. It expects the API server to be running at `http://localhost:8000`.

1. **Install dependencies**

   ```bash
   cd frontend
   npm install
   ```

2. **Run the dev server**

   ```bash
   npm run dev
   ```

   The UI will be available at [http://localhost:5173](http://localhost:5173).

## Stopping

```bash
docker compose down
```

Add `-v` to also delete the Postgres data volume (wipes the database).

## Search ranking

`backend/search/index.py` scores documents with BM25, which builds on TF-IDF by additionally saturating term frequency and normalizing for document length. Query tokens are deduplicated first, so a term repeated in the query is only scored once.

Each distinct query term contributes a score against the **body** index:

```
score(D, Q) = Σ IDF(qi) · f(qi, D) · (k1 + 1)
                ─────────────────────────────────────
                f(qi, D) + k1 · (1 - b + b · |D| / avgdl)
```

- `f(qi, D)` — how many times query term `qi` occurs in document `D`
- `|D|` / `avgdl` — length of `D` (in body tokens) and the average document length across the corpus
- `k1` (typically 1.2–2.0; `1.5` here) — controls term-frequency saturation; higher values let repeated terms keep adding score for longer
- `b` (typically 0.75; `0.75` here) — controls how strongly document length is normalized; `0` disables length normalization, `1` applies it fully
- `IDF(qi)` — inverse document frequency, computed with the standard BM25 form `ln((N - n(qi) + 0.5) / (n(qi) + 0.5))`, where `N` is the total number of documents and `n(qi)` is the number of documents containing `qi`

### Title boosting

Titles are indexed separately from body text, and a term matching a document's title adds a second contribution on top of the body score:

```
title_score(D, Q) = Σ IDF(qi) · f(qi, title(D)) · (k1 + 1)
                      ──────────────────────────────
                          f(qi, title(D)) + k1
```

Titles are short and roughly uniform in length, so there is no length normalization here (equivalently, `b = 0`); `IDF` is computed over the title index. A document matching in both title and body therefore ranks above one matching in body alone.

## Evaluation

`backend/eval/benchmark.json` holds a hand-judged relevance set for measuring ranking changes against the 100-document corpus: 30 queries across categories (entity lookups, multi-term, team, championship/finals, historical events, strategy, ambiguous), each with graded relevance judgements (`0`–`3`) and a short reason per judged document.

`evaluation_config` records how the judgements are meant to be scored — binary relevance at `>= 2`, metrics at `k = 1, 3, 5`, exponential nDCG gain with the ideal ranking taken from the judged pool, unjudged documents treated as non-relevant, and documents keyed by their `source_file` in `data/documents/`.

### Running the eval

With the API server running (see [Run the API server](#setup)):

```bash
cd backend
uv run eval/eval.py
```

This queries `/search` for every benchmark query, computes MRR, precision@k, and nDCG@k (overall and per-query), and writes a timestamped run file to `backend/eval/runs/`.

## Project layout

```
backend/
  main.py               # FastAPI app & routes (including /search)
  database.py           # SQLAlchemy engine/session setup
  models.py             # SQLAlchemy ORM models
  schemas.py            # Pydantic request/response schemas
  ingest_documents.py   # Loads JSON documents from data/documents/ into the database
  index_documents.py    # Builds the in-memory inverted index from documents at startup
  search/
    tokenizer.py        # Lowercases & splits text into unicode word tokens
    index.py            # Inverted title/body indexes & BM25 search ranking
  eval/
    benchmark.json      # Judged query/relevance set for evaluating ranking changes
    eval.py             # Runs the benchmark against /search and writes a run file
    metrics.py          # MRR, precision@k, nDCG@k implementations
    runs/               # Timestamped output files from eval.py runs
frontend/
  index.html               # Vite entry page
  src/
    main.jsx               # React entry point
    App.jsx                # React search UI, queries the /search endpoint
    index.css              # UI styles
  vite.config.js           # Vite dev server config
scripts/
  fetch_wikipedia_corpus.py  # Fetches the curated basketball corpus from Wikipedia into data/documents/
data/
  documents/               # Sample documents (JSON) used by ingest_documents.py
  metadata.json            # Metadata about the fetched corpus
docker-compose.yml         # Local Postgres container
```
