# SPARQL endpoint for RDFLib custom functions ✨️🐍

A SPARQL endpoint to serve machine learning models, or any other logic implemented in Python.

Built with RDFLib and FastAPI, CORS enabled.

* See `app/function_openpredict.py` for examples to define a custom SPARQL function for RDFLib graphs.

* Register the functions in the get `sparql_endpoint` function in `app/main.py` with:

  * ```python
    rdflib.plugins.sparql.CUSTOM_EVALS['SPARQL_openpredict_prediction'] = SPARQL_openpredict_prediction
    ```

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

Use this federated query to retrieve predicted treatments for a drug or disease (OMIM or DRUGBANK) from any other SPARQL endpoint supporting federated queries.

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

