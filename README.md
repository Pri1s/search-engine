# Search Engine

A domain-specific (vertical) search engine. Currently a FastAPI backend backed by PostgreSQL, with basic document create/read endpoints.

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

## Stopping

```bash
docker compose down
```

Add `-v` to also delete the Postgres data volume (wipes the database).

## Project layout

```
backend/
  main.py        # FastAPI app & routes
  database.py     # SQLAlchemy engine/session setup
  models.py       # SQLAlchemy ORM models
  schemas.py      # Pydantic request/response schemas
docker-compose.yml # Local Postgres container
```
