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

Error with OpenLink Virtuoso:

> ```
> Virtuoso 22003 Error SR017: aref: Bad array subscript (zero-based) 2 for an arg of type ARRAY_OF_POINTER (193) and length 1.
> ```

No results with Ontotext GraphDB:

> ```
> {
>   "head": {
>     "vars": [
>       "label1",
>       "label2",
>       "concat"
>     ]
>   },
>   "results": {
>     "bindings": []
>   }
> }
> ```

According to [W3C docs about Federated queries](https://www.w3.org/TR/2013/REC-sparql11-federated-query-20130321/#defn_service):

> The evaluation of `SERVICE` is defined in terms of the [SPARQL Results](http://www.w3.org/TR/rdf-sparql-XMLres/) [[RESULTS](https://www.w3.org/TR/2013/REC-sparql11-federated-query-20130321/#RESULTS)] returned by a SPARQL Protocol [[SPROT](https://www.w3.org/TR/2013/REC-sparql11-federated-query-20130321/#SPROT)] execution of the nested graph pattern:
