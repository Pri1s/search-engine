FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

WORKDIR /app/backend

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project

COPY . .
RUN uv sync --frozen

CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
