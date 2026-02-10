# Example SPARQL endpoint for Python function

A SPARQL endpoint to serve any other logic implemented in Python.

> Built with [RDFLib](https://github.com/RDFLib/rdflib) and [FastAPI](https://fastapi.tiangolo.com/), CORS enabled.

## ✨️ Run

> Requirements: [`uv`](https://docs.astral.sh/uv/getting-started/installation/) to easily handle scripts and virtual environments.

Run the server on http://localhost:8000

```sh
uv run uvicorn main:app --reload
```

## 🐳 Run with docker

Checkout the `Dockerfile` to see how the image is built, and run it with the `compose.yml`:

```sh
docker compose up -d --build
```

## 📬 Example query

Concatenate the 2 given string, and also return the length as additional Length variable

```sparql
PREFIX myfunctions: <https://w3id.org/sparql-functions/>
SELECT ?concat ?concatLength WHERE {
    BIND("First" AS ?first)
    BIND(myfunctions:custom_concat(?first, "last") AS ?concat)
}
```
