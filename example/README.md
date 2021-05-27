# Example SPARQL endpoint for ML classifier ✨️🐍

A SPARQL endpoint to serve machine learning models, or any other logic implemented in Python. Serve drug/disease predictions using the OpenPredict package.

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

