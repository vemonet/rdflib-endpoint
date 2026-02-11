FROM ghcr.io/astral-sh/uv:python3.14-alpine

COPY . /app/
WORKDIR /app/

RUN uv sync

ENV PYTHONUNBUFFERED='1'
EXPOSE 80
ENTRYPOINT ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80", "--workers", "4"]
