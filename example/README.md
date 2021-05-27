# Example SPARQL endpoint for ML classifier ✨️🐍

A SPARQL endpoint to serve machine learning models, or any other logic implemented in Python. Serve drug/disease predictions using the OpenPredict classifier.

Built with [RDFLib](https://github.com/RDFLib/rdflib) and [FastAPI](https://fastapi.tiangolo.com/), CORS enabled.

## Install and run ✨️

1. Install dependencies

```bash
pip install -r requirements.txt
```

2. Run the server on http://localhost:8000

```bash
uvicorn main:app --reload --app-dir app
```

## Or run with docker 🐳

Checkout the `Dockerfile` to see how the image is built, and run it with the `docker-compose.yml`:

```bash
docker-compose up -d --build
```

Or build and run with docker:

```bash
docker build -t rdflib-endpoint .
# Run locally
docker run -e VIRTUAL_HOST=sparql-openpredict.137.120.31.102.nip.io -e VIRTUAL_PORT=80 rdflib-endpoint

# Or using a reverse nginx-proxy
docker run -e VIRTUAL_HOST=sparql-openpredict.137.120.31.102.nip.io -e VIRTUAL_PORT=80 rdflib-endpoint
```

Run on http://localhost:8080

```bash
docker run -p 8080:80 rdflib-endpoint
```

Run using a reverse [nginx-proxy](https://github.com/nginx-proxy/nginx-proxy)

```bash
docker run -it -e VIRTUAL_HOST=sparql-openpredict.137.120.31.102.nip.io -e VIRTUAL_PORT=80 rdflib-endpoint
```

## Try a federated query 📬

Use this federated query to retrieve predicted treatments for a drug or disease (OMIM or DRUGBANK) from any other SPARQL endpoint supporting federated queries (note that this query use our test SPARQL endpoints, it might not be always up)

```SPARQL
PREFIX openpredict: <https://w3id.org/um/openpredict/>
SELECT * WHERE
{
  SERVICE <https://sparql-openpredict.137.120.31.102.nip.io/sparql> {
	SELECT ?drugOrDisease ?predictedForTreatment WHERE {
    	BIND("OMIM:246300" AS ?drugOrDisease)
    	BIND(openpredict:prediction(?drugOrDisease) AS ?predictedForTreatment)
	}
  }
}
```

