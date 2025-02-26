FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim
# Used only for testing federated queries from various triplestores

COPY . /app/
WORKDIR /app/

RUN uv sync --all-extras

ENV PYTHONUNBUFFERED='1'

EXPOSE 80
ENTRYPOINT ["uv", "run", "uvicorn", "example.main:app", "--host", "0.0.0.0", "--port", "80", "--workers", "2"]
