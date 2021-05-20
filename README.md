# SPARQL endpoint for Python functions

A SPARQL endpoint to serve machine learning models, or any other logic implemented in Python.

Built with FastAPI and RDFLib.

## Install and run

1. Install dependencies

```bash
pip install -r requirements.txt
```

2. Run the server on http://localhost:8000

```bash
uvicorn main:app --reload --app-dir app
```

## Or run with docker

```bash
docker-compose up -d --build
```

## Try a federated query

```SPARQL
PREFIX openpredict: <https://w3id.org/um/openpredict/>

SELECT * WHERE
{
  SERVICE <https://sparql-openpredict.137.120.31.102.nip.io/sparql> {

    SELECT ?label1 ?label2 ?concat WHERE {
        BIND("Hello" AS ?label1)
        BIND("World" AS ?label2)
      BIND(openpredict:similarity(?label1, ?label2) AS ?concat)
    }
  }
}
```

