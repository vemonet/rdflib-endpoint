# Example SPARQL endpoint for Python function

A SPARQL endpoint to serve machine learning models, or any other logic implemented in Python. Serve drug/disease predictions using the OpenPredict classifier.

Built with [RDFLib](https://github.com/RDFLib/rdflib) and [FastAPI](https://fastapi.tiangolo.com/), CORS enabled.

## Example queries 📬

### Get predictions

Concatenate the 2 given string, and also return the length as additional Length variable

```SPARQL
PREFIX myfunctions: <https://w3id.org/um/sparql-functions/>
SELECT ?concat ?concatLength WHERE {
    BIND("First" AS ?first)
    BIND(myfunctions:custom_concat(?first, "last") AS ?concat)
}
```

### Try a federated query

Use this federated query to retrieve predicted treatments for a drug or disease (OMIM or DRUGBANK) from any other SPARQL endpoint supporting federated queries (note that this query use our test SPARQL endpoints, it might not be always up)

**From another SPARQL endpoint:**

```SPARQL
PREFIX myfunctions: <https://w3id.org/um/sparql-functions/>
SELECT * WHERE
{
  SERVICE <https://service.openpredict.137.120.31.102.nip.io/sparql> {
    SELECT ?concat ?concatLength WHERE {
        BIND("First" AS ?first)
        BIND(myfunctions:custom_concat(?first, "last") AS ?concat)
    }
  }
}
```

**From the RDFLib SPARQL endpoint**

⚠️ RDFLib has a few limitation related to federated queries:

* Unfortunately, the `PREFIX` keyword can crash with federated queries in RDFLib, so we need to write the full URIs

* The latest version of RDFLib (`5.0.0 `) only recognize **lowercase `service`**. This will be fixed in the next versions.

Run this federated query on the RDFLib endpoint https://service.translator.137.120.31.102.nip.io to resolve drug/disease labels retrieved from the Nanopublication network:

```SPARQL
SELECT DISTINCT ?label ?subject ?object (<https://w3id.org/um/translator/get_label>(str(?subject)) AS ?subjectLabel) (<https://w3id.org/um/translator/get_label>(str(?object)) AS ?objectLabel)
WHERE {
  	service <http://virtuoso.np.dumontierlab.137.120.31.101.nip.io/sparql> {
        SELECT * WHERE {
            GRAPH ?np_assertion {
              ?association <http://www.w3.org/2000/01/rdf-schema#label> ?label ;
                <http://www.w3.org/1999/02/22-rdf-syntax-ns#subject> ?subject ;
                <http://www.w3.org/1999/02/22-rdf-syntax-ns#predicate> ?predicate ;
                <http://www.w3.org/1999/02/22-rdf-syntax-ns#object> ?object .
              optional {
                ?association <https://w3id.org/biolink/vocab/relation> ?relation .
              }
              optional {
                ?association <https://w3id.org/biolink/vocab/provided_by> ?provided_by .
              }
              optional {
                ?association <https://w3id.org/biolink/vocab/association_type> ?association_type .
              }
              ?subject <https://w3id.org/biolink/vocab/category> ?subject_category .
              ?object <https://w3id.org/biolink/vocab/category> ?object_category .
            }
            filter ( ?subject_category = <https://w3id.org/biolink/vocab/Drug> || ?subject_category = <https://w3id.org/biolink/vocab/ChemicalSubstance> )
            filter ( ?object_category = <https://w3id.org/biolink/vocab/Disease> )
            GRAPH ?np_head {
                ?np_uri <http://www.nanopub.org/nschema#hasAssertion> ?np_assertion .
            }
                ?np_uri <http://purl.org/dc/terms/creator> <https://orcid.org/0000-0002-7641-6446> .
            	filter NOT EXISTS { ?creator <http://purl.org/nanopub/x/retracts> ?np_uri }
        } LIMIT 5
  	}
}
```

### Insert data

Insert data in the in-memory rdflib graph:

```SPARQL
INSERT DATA {
    <http://subject> <http://predicate> <http://object> .
}
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

Or build and run with docker:

```bash
docker build -t rdflib-endpoint .
```

Run on http://localhost:8080

```bash
docker run -p 8080:80 rdflib-endpoint
```

