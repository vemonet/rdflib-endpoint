# SPARQL endpoint for RDFLib custom functions

[![Run tests](https://github.com/vemonet/rdflib-endpoint/actions/workflows/run-tests.yml/badge.svg)](https://github.com/vemonet/rdflib-endpoint/actions/workflows/run-tests.yml) [![CodeQL](https://github.com/vemonet/rdflib-endpoint/actions/workflows/codeql-analysis.yml/badge.svg)](https://github.com/vemonet/rdflib-endpoint/actions/workflows/codeql-analysis.yml)

A SPARQL endpoint based on a RDFLib Graph to easily serve machine learning models, or any other logic implemented in Python via custom SPARQL functions. It can also be used to expose a RDFLib Graph as a SPARQL endpoint, with or without custon functions.

The deployed SPARQL endpoint can be used as a `SERVICE <https://your-endpoint-url/sparql>` in a federated SPARQL query from regular triplestores. Tested on OpenLink Virtuoso (Jena based) and Ontotext GraphDB (rdf4j based), it is also CORS enabled.

Only `SELECT` queries are currently supported, which is enough to support federated queries. Feel free to create an [issue](/issues), or send a pull request if you would like to see it implemented.

Built with [RDFLib](https://github.com/RDFLib/rdflib) and [FastAPI](https://fastapi.tiangolo.com/). Tested for python 3.6, 3.7 and 3.8

## Install the package 📥

Simply install directly from GitHub:

```bash
pip install rdflib-endpoint@git+https://github.com/vemonet/rdflib-endpoint@main
```

> Let us know in the [issues](/issues) if you would be interested for this package to be published to PyPI.

Or clone and install locally for development:

```bash
git clone https://github.com/vemonet/rdflib-endpoint
cd rdflib-endpoint
pip install -e .
```

## Define custom SPARQL functions 🐍

Create a `app/main.py` file in your project folder with your functions and endpoint parameters:

```python
from rdflib_endpoint import SparqlEndpoint
import rdflib
from rdflib.plugins.sparql.evalutils import _eval

def custom_concat(query_results, ctx, part, eval_part):
    """
    Concat 2 strings in the 2 senses and return the length as additional Length variable

    Query:
    PREFIX myfunctions: <https://w3id.org/um/sparql-functions/>
    SELECT ?concat ?concatLength WHERE {
        BIND("First" AS ?first)
        BIND(myfunctions:custom_concat(?first, "last") AS ?concat)
    }
    """
    argument1 = str(_eval(part.expr.expr[0], eval_part.forget(ctx, _except=part.expr._vars)))
    argument2 = str(_eval(part.expr.expr[1], eval_part.forget(ctx, _except=part.expr._vars)))
    evaluation = []
    scores = []
    concat_string = argument1 + argument2
    reverse_string = argument2 + argument1
    evaluation.append(concat_string)
    evaluation.append(reverse_string)
    scores.append(len(concat_string))
    scores.append(len(reverse_string))
    # Append the results for our custom function
    for i, result in enumerate(evaluation):
        query_results.append(eval_part.merge({
            part.var: rdflib.Literal(result), 
            rdflib.term.Variable(part.var + 'Length'): rdflib.Literal(scores[i])
        }))
    return query_results, ctx, part, eval_part

# Start the SPARQL endpoint based on a RDFLib Graph and register your custom functions
g = rdflib.Graph()
app = SparqlEndpoint(
    graph=g,
    functions={
        'https://w3id.org/um/sparql-functions/custom_concat': custom_concat
    },
    title="SPARQL endpoint for RDFLib graph", 
    description="A SPARQL endpoint to serve machine learning models, or any other logic implemented in Python. \n[Source code](https://github.com/vemonet/rdflib-endpoint)",
    version="0.0.1",
    public_url='https://your-endpoint-url/sparql',
    cors_enabled=True
)
```

Checkout the [`example`](https://github.com/vemonet/rdflib-endpoint/tree/main/example) folder for a complete working app example to get started, with docker-compose deployment. The best way to create a new SPARQL endpoint is to copy this `example` folder and start from it.

## Run the SPARQL endpoint 🦄

Run the FastAPI server from the root folder with `uvicorn` on http://localhost:8000 

```bash
cd example
uvicorn main:app --reload --app-dir app
```

## Run the tests ✅️

Install additional dependencies:

```bash
pip install pytest requests
```

Run the tests locally:

```bash
pytest -s
```

## Projects using rdflib-endpoint 📂

Some projects using rdflib-endpoint to deploy custom SPARQL endpoints with python:

* https://github.com/MaastrichtU-IDS/openpredict-sparql-service
  * Serve predicted biomedical entities associations (e.g. disease treated by drug) using the OpenPredict classifier
* https://github.com/vemonet/translator-sparql-service
  * A SPARQL endpoint to serve NCATS Translator services as SPARQL custom functions.
