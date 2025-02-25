<div align="center">

# 💫 SPARQL endpoint for RDFLib

[![PyPI - Version](https://img.shields.io/pypi/v/rdflib-endpoint.svg?logo=pypi&label=PyPI&logoColor=silver)](https://pypi.org/project/rdflib-endpoint/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/rdflib-endpoint.svg?logo=python&label=Python&logoColor=silver)](https://pypi.org/project/rdflib-endpoint/)

[![Test package](https://github.com/vemonet/rdflib-endpoint/actions/workflows/test.yml/badge.svg)](https://github.com/vemonet/rdflib-endpoint/actions/workflows/test.yml)
[![Publish package](https://github.com/vemonet/rdflib-endpoint/actions/workflows/release.yml/badge.svg)](https://github.com/vemonet/rdflib-endpoint/actions/workflows/release.yml)
[![Coverage Status](https://coveralls.io/repos/github/vemonet/rdflib-endpoint/badge.svg?branch=main)](https://coveralls.io/github/vemonet/rdflib-endpoint?branch=main)

[![license](https://img.shields.io/pypi/l/rdflib-endpoint.svg?color=%2334D058)](https://github.com/vemonet/rdflib-endpoint/blob/main/LICENSE.txt)
[![types - Mypy](https://img.shields.io/badge/types-mypy-blue.svg)](https://github.com/python/mypy)

</div>

`rdflib-endpoint` is a SPARQL endpoint based on RDFLib to **easily serve RDF files locally**, machine learning models, or any other logic implemented in Python via **custom SPARQL functions**.

It aims to enable python developers to easily deploy functions that can be queried in a federated fashion using SPARQL. For example: using a python function to resolve labels for specific identifiers, or run a classifier given entities retrieved using a `SERVICE` query to another SPARQL endpoint.

> Feel free to create an [issue](/issues), or send a pull request if you are facing issues or would like to see a feature implemented.

## ℹ️ How it works

`rdflib-endpoint` can be used directly from the terminal to quickly serve RDF files through a SPARQL endpoint automatically deployed locally.

It can also be used to define custom SPARQL functions: the user defines and registers custom SPARQL functions, and/or populate the RDFLib Graph using Python, then the endpoint is started using `uvicorn`.

The deployed SPARQL endpoint can be used as a `SERVICE` in a federated SPARQL query from regular triplestores SPARQL endpoints. Tested on OpenLink Virtuoso (Jena based) and Ontotext GraphDB (RDF4J based). The endpoint is CORS enabled by default to enable querying it from client JavaScript (can be turned off).

> Built with [RDFLib](https://github.com/RDFLib/rdflib) and [FastAPI](https://fastapi.tiangolo.com/).

## 📦️ Installation

This package requires Python >=3.8, install it  from [PyPI](https://pypi.org/project/rdflib-endpoint/) with:

```shell
pip install rdflib-endpoint
```

The `uvicorn` and `gunicorn` dependencies are not included by default, if you want to install them use the optional dependency `web`:

```bash
pip install "rdflib-endpoint[web]"
```

If you want to use `rdlib-endpoint` as a CLI you can install with the optional dependency `cli`:

```bash
pip install "rdflib-endpoint[cli]"
```

If you want to use [oxigraph](https://github.com/oxigraph/oxigraph) as backend triplestore you can install with the optional dependency `oxigraph`:

```bash
pip install "rdflib-endpoint[cli,oxigraph]"
```

> [!WARNING]
> Oxigraph and `oxrdflib` do not support custom functions, so it can be only used to deploy graphs without custom functions.

## ⌨️ Use the CLI

`rdflib-endpoint` can be used from the command line interface to perform basic utility tasks, such as serving or converting RDF files locally.

Make sure you installed `rdflib-endpoint` with the `cli` optional dependencies:

```bash
pip install "rdflib-endpoint[cli]"
```

### ⚡️ Quickly serve RDF files through a SPARQL endpoint

Use `rdflib-endpoint` as a command line interface (CLI) in your terminal to quickly serve one or multiple RDF files as a SPARQL endpoint.

You can use wildcard and provide multiple files, for example to serve all turtle, JSON-LD and nquads files in the current folder you could run:

```bash
rdflib-endpoint serve *.ttl *.jsonld *.nq
```

> Then access the YASGUI SPARQL editor on http://localhost:8000

If you installed with the Oxigraph optional dependency you can use it as backend triplestore, it is faster and supports some functions that are not supported by the RDFLib query engine (such as `COALESCE()`):

```bash
rdflib-endpoint serve --store Oxigraph "*.ttl" "*.jsonld" "*.nq"
```

### 🔄 Convert RDF files to another format

`rdflib-endpoint` can also be used to quickly merge and convert files from multiple formats to a specific format:

```bash
rdflib-endpoint convert "*.ttl" "*.jsonld" "*.nq" --output "merged.trig"
```

## ✨ Deploy your SPARQL endpoint

`rdflib-endpoint` enables you to easily define and deploy SPARQL endpoints based on RDFLib Graph, and Dataset. Additionally it provides helpers to defines custom functions in the endpoint.

Checkout the [`example`](https://github.com/vemonet/rdflib-endpoint/tree/main/example) folder for a complete working app example to get started, including a docker deployment. A good way to create a new SPARQL endpoint is to copy this `example` folder, and start from it.

### 🚨 Deploy as a standalone API

Deploy your SPARQL endpoint as a standalone API:

```python
from rdflib import Dataset
from rdflib_endpoint import SparqlEndpoint

# Start the SPARQL endpoint based on a RDFLib Graph and register your custom functions
g = Dataset()
# TODO: Add triples in your graph

# Then use either SparqlEndpoint or SparqlRouter, they take the same arguments
app = SparqlEndpoint(
    graph=g,
    path="/",
    cors_enabled=True,
    # Metadata used for the SPARQL service description and Swagger UI:
    title="SPARQL endpoint for RDFLib graph",
    description="A SPARQL endpoint to serve machine learning models, or any other logic implemented in Python. \n[Source code](https://github.com/vemonet/rdflib-endpoint)",
    version="0.1.0",
    public_url='https://your-endpoint-url/',
    # Example query displayed in YASGUI default tab
    example_query="""PREFIX myfunctions: <https://w3id.org/um/sparql-functions/>
SELECT ?concat ?concatLength WHERE {
    BIND("First" AS ?first)
    BIND(myfunctions:custom_concat(?first, "last") AS ?concat)
}""",
    # Additional example queries displayed in additional YASGUI tabs
    example_queries = {
    	"Bio2RDF query": {
        	"endpoint": "https://bio2rdf.org/sparql",
        	"query": """SELECT DISTINCT * WHERE {
    ?s a ?o .
} LIMIT 10""",
    	},
    	"Custom function": {
        	"query": """PREFIX myfunctions: <https://w3id.org/um/sparql-functions/>
SELECT ?concat ?concatLength WHERE {
    BIND("First" AS ?first)
    BIND(myfunctions:custom_concat(?first, "last") AS ?concat)
}""",
    	}
	}
)
```

Finally deploy this app using `uvicorn` (see below)

### 🛣️ Deploy as a router to include in an existing API

Deploy your SPARQL endpoint as an `APIRouter` to include in an existing `FastAPI` API. The `SparqlRouter` constructor takes the same arguments as the `SparqlEndpoint`, apart from `enable_cors` which needs be enabled at the API level.

```python
from fastapi import FastAPI
from rdflib import Dataset
from rdflib_endpoint import SparqlRouter

g = Dataset()
sparql_router = SparqlRouter(
    graph=g,
    path="/",
    # Metadata used for the SPARQL service description and Swagger UI:
    title="SPARQL endpoint for RDFLib graph",
    description="A SPARQL endpoint to serve machine learning models, or any other logic implemented in Python. \n[Source code](https://github.com/vemonet/rdflib-endpoint)",
    version="0.1.0",
    public_url='https://your-endpoint-url/',
)

app = FastAPI()
app.include_router(sparql_router)
```

> To deploy this route in a **Flask** app checkout how it has been done in the [curies mapping service](https://github.com/biopragmatics/curies/blob/main/src/curies/mapping_service/api.py) of the [Bioregistry](https://bioregistry.io/).

### 📝 Define custom SPARQL functions

This option makes it easier to define functions in your SPARQL endpoint, e.g. `BIND(myfunction:custom_concat("start", "end") AS ?concat)`. It can be used with the `SparqlEndpoint` and `SparqlRouter` classes.

Create a `app/main.py` file in your project folder with your custom SPARQL functions, and endpoint parameters:

````python
import rdflib
from rdflib import Dataset
from rdflib.plugins.sparql.evalutils import _eval
from rdflib_endpoint import SparqlEndpoint

def custom_concat(query_results, ctx, part, eval_part):
    """Concat 2 strings in the 2 senses and return the length as additional Length variable
    """
    # Retrieve the 2 input arguments
    argument1 = str(_eval(part.expr.expr[0], eval_part.forget(ctx, _except=part.expr._vars)))
    argument2 = str(_eval(part.expr.expr[1], eval_part.forget(ctx, _except=part.expr._vars)))
    evaluation = []
    scores = []
    # Prepare the 2 result string, 1 for eval, 1 for scores
    evaluation.append(argument1 + argument2)
    evaluation.append(argument2 + argument1)
    scores.append(len(argument1 + argument2))
    scores.append(len(argument2 + argument1))
    # Append the results for our custom function
    for i, result in enumerate(evaluation):
        query_results.append(eval_part.merge({
            part.var: rdflib.Literal(result),
            # With an additional custom var for the length
            rdflib.term.Variable(part.var + 'Length'): rdflib.Literal(scores[i])
        }))
    return query_results, ctx, part, eval_part

# Start the SPARQL endpoint based on a RDFLib Graph and register your custom functions
g = Dataset(default_union=True)
# Use either SparqlEndpoint or SparqlRouter, they take the same arguments
app = SparqlEndpoint(
    graph=g,
    path="/",
    # Register the functions:
    functions={
        'https://w3id.org/um/sparql-functions/custom_concat': custom_concat
    },
    cors_enabled=True,
    # Metadata used for the SPARQL service description and Swagger UI:
    title="SPARQL endpoint for RDFLib graph",
    description="A SPARQL endpoint to serve machine learning models, or any other logic implemented in Python. \n[Source code](https://github.com/vemonet/rdflib-endpoint)",
    version="0.1.0",
    public_url='https://your-endpoint-url/',
    # Example queries displayed in the Swagger UI to help users try your function
    example_query="""PREFIX myfunctions: <https://w3id.org/um/sparql-functions/>
SELECT ?concat ?concatLength WHERE {
    BIND("First" AS ?first)
    BIND(myfunctions:custom_concat(?first, "last") AS ?concat)
}"""
)
````

### ✒️ Or directly define the custom evaluation

You can also directly provide the custom evaluation function, this will override the `functions`.

Refer to the [RDFLib documentation](https://rdflib.readthedocs.io/en/stable/_modules/examples/custom_eval.html) to define the custom evaluation function. Then provide it when instantiating the SPARQL endpoint:

```python
import rdflib
from rdflib.plugins.sparql.evaluate import evalBGP
from rdflib.namespace import FOAF, RDF, RDFS

def custom_eval(ctx, part):
    """Rewrite triple patterns to get super-classes"""
    if part.name == "BGP":
        # rewrite triples
        triples = []
        for t in part.triples:
            if t[1] == RDF.type:
                bnode = rdflib.BNode()
                triples.append((t[0], t[1], bnode))
                triples.append((bnode, RDFS.subClassOf, t[2]))
            else:
                triples.append(t)
        # delegate to normal evalBGP
        return evalBGP(ctx, triples)
    raise NotImplementedError()

app = SparqlEndpoint(
    graph=g,
    custom_eval=custom_eval
)
```

### 🦄 Run the SPARQL endpoint

You can then run the SPARQL endpoint server from the folder where your script is defined with `uvicorn` on http://localhost:8000

```bash
cd example
uv run uvicorn app.main:app --reload
```

> Checkout in the `example/README.md` for more details, such as deploying it with docker.

## 📂 Projects using rdflib-endpoint

Here are some projects using `rdflib-endpoint` to deploy custom SPARQL endpoints with python:

* [The Bioregistry](https://bioregistry.io/), an open source, community curated registry, meta-registry, and compact identifier resolver.
* [proycon/codemeta-server](https://github.com/proycon/codemeta-server), server for codemeta, in memory triple store, SPARQL endpoint and simple web-based visualisation for end-user.
* [AKSW/sparql-file](https://github.com/AKSW/sparql-file), serve a RDF file as an RDFLib Graph through a SPARQL endpoint.

## 🛠️ Contributing

To run the project in development and make a contribution checkout the [contributing page](https://github.com/vemonet/rdflib-endpoint/blob/main/CONTRIBUTING.md).
