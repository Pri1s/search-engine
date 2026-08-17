# Search Engine

A domain-specific (vertical) search engine, currently focused on basketball. A FastAPI backend backed by PostgreSQL, with document create/read endpoints, a JSON-based ingestion script, and a work-in-progress inverted index for search.

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
uv run ingest_docs.py
```

## Stopping

```bash
docker compose down
```

Add `-v` to also delete the Postgres data volume (wipes the database).

## Search ranking

`backend/search/index.py` currently scores documents with TF-IDF and is being extended toward BM25, which additionally saturates term frequency and normalizes for document length:

```
score(D, Q) = Σ IDF(qi) · f(qi, D) · (k1 + 1)
                ─────────────────────────────────────
                f(qi, D) + k1 · (1 - b + b · |D| / avgdl)
```

- `f(qi, D)` — how many times query term `qi` occurs in document `D`
- `|D|` / `avgdl` — length of `D` (in tokens) and the average document length across the corpus
- `k1` (typically 1.2–2.0) — controls term-frequency saturation; higher values let repeated terms keep adding score for longer
- `b` (typically 0.75) — controls how strongly document length is normalized; `0` disables length normalization, `1` applies it fully
- `IDF(qi)` — inverse document frequency, typically `ln((N - n(qi) + 0.5) / (n(qi) + 0.5) + 1)`, where `N` is the total number of documents and `n(qi)` is the number of documents containing `qi`

## Project layout

```
backend/
  main.py           # FastAPI app & routes
  database.py       # SQLAlchemy engine/session setup
  models.py         # SQLAlchemy ORM models
  schemas.py        # Pydantic request/response schemas
  ingest_docs.py    # Loads JSON documents from data/documents/ into the database
  search/
    index.py        # Inverted index for search ranking (work in progress, not yet wired into the API)
data/
  documents/         # Sample documents (JSON) used by ingest_docs.py
docker-compose.yml   # Local Postgres container
```
