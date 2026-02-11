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

`rdflib-endpoint` is a SPARQL endpoint based on RDFLib, use it to easily:

- **serve local RDF files** in one command,
- **expose custom SPARQL functions** implemented in python that can be queried in a federated fashion using SPARQL `SERVICE` from another endpoint.

> Feel free to create an [issue](/issues), or send a pull request if you are facing issues or would like to see a feature implemented.

## 📦️ Installation

This package requires Python >=3.8, install it  from [PyPI](https://pypi.org/project/rdflib-endpoint/) with:

```shell
pip install "rdflib-endpoint[cli,oxigraph]"
# Or install with uv
uv tool install rdflib-endpoint --with "rdflib-endpoint[cli,oxigraph]"
# Or run directly with uvx
uvx --with "rdflib-endpoint[cli,oxigraph]" rdflib-endpoint
```

Optional extras:

| Extra      | Adds                                                     |
| ---------- | -------------------------------------------------------- |
| `web`      | `uvicorn` (not included in default dependencies)         |
| `cli`      | CLI commands and `uvicorn`                               |
| `oxigraph` | [Oxigraph](https://github.com/oxigraph/oxigraph) backend |

## ⌨️ Use the CLI

`rdflib-endpoint` can be used from the command line interface to perform basic utility tasks, such as serving or converting RDF files locally.

**Serve RDF files**, with YASGUI available on http://localhost:8000:

```bash
rdflib-endpoint serve *.ttl *.jsonld *.nq
```

Use [oxigraph](https://github.com/oxigraph/oxigraph) as backend, it supports some functions that are not supported by the RDFLib query engine, such as `COALESCE`:

```bash
rdflib-endpoint serve --store Oxigraph "*.ttl" "*.jsonld" "*.nq"
```

**Convert and merge RDF files** from multiple formats to a specific format:

```bash
rdflib-endpoint convert "*.ttl" "*.jsonld" "*.nq" --output "merged.trig"
```

## ✨ Deploy your SPARQL endpoint

`rdflib-endpoint` enables you to easily define and deploy SPARQL endpoints based on RDFLib Graph and Dataset. Additionally it provides helpers to defines custom functions in the endpoint.

> [!TIP]
>
> Checkout the [`example`](https://github.com/vemonet/rdflib-endpoint/tree/main/example) folder for a complete working app example to get started, including a docker deployment.

### ⚡️ Deploy as a standalone API

Create and run a standalone SPARQL endpoint using `SparqlEndpoint`, e.g. in a `main.py` file:

```python
from rdflib import Dataset
from rdflib_endpoint import SparqlEndpoint

ds = Dataset()

app = SparqlEndpoint(
    graph=ds,
    path="/",
    # CORS enabled by default to enable querying it from client JavaScript
    cors_enabled=True,
    # Metadata used for the SPARQL service description and Swagger UI:
    title="SPARQL endpoint for RDFLib graph",
    description="A SPARQL endpoint to serve any other logic implemented in Python. \n[Source code](https://github.com/vemonet/rdflib-endpoint)",
    version="0.1.0",
    public_url='https://your-endpoint-url/',
    # Example query displayed in YASGUI default tab
    example_query="""PREFIX myfunctions: <https://w3id.org/sparql-functions/>
SELECT ?concat ?concatLength WHERE {
    BIND("First" AS ?first)
    BIND(myfunctions:custom_concat(?first, "last") AS ?concat)
}""",
    # Additional example queries displayed in additional YASGUI tabs
    example_queries = {
    	"Concat function": {
        	"query": """PREFIX myfunctions: <https://w3id.org/sparql-functions/>
SELECT ?concat ?concatLength WHERE {
    BIND(myfunctions:custom_concat("first", "last") AS ?concat)
}""",
    	}
	}
)
```

Start the server on http://localhost:8000:

```sh
uv run uvicorn main:app --reload
```

### 🛣️ Embedding in an existing app

Instead of a full app, you can mount the endpoint as a router. `SparqlRouter` constructor takes the same arguments as `SparqlEndpoint`, apart from `enable_cors` which is defined at the API level.

```python
from fastapi import FastAPI
from rdflib import Dataset
from rdflib_endpoint import SparqlRouter

ds = Dataset()
sparql_router = SparqlRouter(
    graph=ds,
    path="/",
    # Metadata used for the SPARQL service description and Swagger UI:
    title="SPARQL endpoint for RDFLib graph",
)

app = FastAPI()
app.include_router(sparql_router)
```

> [!TIP]
>
> To deploy this route in a **Flask** app checkout how it has been done in the [curies mapping service](https://github.com/biopragmatics/curies/blob/main/src/curies/mapping_service/api.py) of the [Bioregistry](https://bioregistry.io/).

### 🧩 Custom SPARQL Functions using decorators

`DatasetExt` extends RDFLib `Dataset` with four decorator helpers to register python-based SPARQL evaluation functions.

| Decorator             | Triggered by                                        | Typical use                         |
| --------------------- | --------------------------------------------------- | ----------------------------------- |
| `@type_function`      | A triple pattern with subject typed by the function | Structured multi-field results      |
| `@predicate_function` | A predicate in the given namespace                  | Fill object values via Python logic |
| `@extension_function` | `BIND(func:myFunc(...))`                            | Scalar or multi-binding functions   |
| `@graph_function`     | `BIND(func:funcGraph(...) AS ?g)`                   | Return a temporary graph            |

Key behaviors:

- Types, predicates and functions IRIs are generated from the provided namespace concatenated to their python counterpart following SPARQL naming conventions (classes in PascalCase, predicates and functions in camelCase)
- Return a list to emit multiple result rows
- Return dataclasses to populate multiple variables.
- Python defaults handle missing input values.

#### `type_function` · Typed triple-pattern functions

Register a triple-pattern function, ideal for complex functions as all inputs/outputs are explicit in the SPARQL query. The function is selected when a subject is typed with the function name in PascalCase in the given namespace. The decorated function receives arguments extracted from input predicates derived from the arguments names, and returns either a single result or a list of results.

```python
from dataclasses import dataclass
from rdflib import Namespace
from rdflib_endpoint import DatasetExt

ds = DatasetExt()

@dataclass
class SplitterResult:
    splitted: str
    index: int

@ds.type_function(namespace=Namespace("https://w3id.org/sparql-functions/"))
def string_splitter(
    split_string: str,
    separator: str = " ",
) -> list[SplitterResult]:
    """Split a string and return each part with their index."""
    split = split_string.split(separator)
    return [SplitterResult(splitted=part, index=idx) for idx, part in enumerate(split)]
```

Example query:

```SPARQL
PREFIX func: <https://w3id.org/sparql-functions/>
SELECT ?input ?part ?idx
WHERE {
    VALUES ?input { "hello world" "cheese is good" }
    [] a func:StringSplitter ;
        func:splitString ?input ;
        func:separator " " ;
        func:splitted ?part ;
        func:index ?idx .
}
```

#### `predicate_function` · Predicate evaluation

Register a predicate function, ideal when the input is a simple IRI. The function is selected when the predicate IRI is in the given namespace. The decorated function receives the subject IRI as input and returns the object values.

```python
import bioregistry
from rdflib import DC, OWL, URIRef
from rdflib_endpoint import DatasetExt

ds = DatasetExt()
conv = bioregistry.get_converter()

@ds.predicate_function(namespace=DC._NS)
def identifier(input_iri: URIRef) -> URIRef:
    """Get the standardized IRI for a given input IRI."""
    return URIRef(conv.standardize_uri(input_iri))

@ds.predicate_function(namespace=OWL._NS)
def same_as(input_iri: URIRef) -> list[URIRef]:
    """Get all alternative IRIs for a given IRI using the Bioregistry."""
    prefix, identifier = conv.compress(input_iri).split(":", 1)
    return [URIRef(iri) for iri in bioregistry.get_providers(prefix, identifier).values()]
```

Example queries:

```sparql
PREFIX dc: <http://purl.org/dc/elements/1.1/>
SELECT ?id WHERE {
    <https://identifiers.org/CHEBI/1> dc:identifier ?id .
}
```

```sparql
PREFIX owl: <http://www.w3.org/2002/07/owl#>
SELECT ?sameAs WHERE {
    <https://identifiers.org/CHEBI/1> owl:sameAs ?sameAs .
}
```

#### `extension_function` · Standard SPARQL extension functions

Register a SPARQL extension function usable with `BIND(<namespace+name>(...) AS ?var)`. The Python function receives evaluated args, returning a list emits multiple bound values.

```python
from dataclasses import dataclass
from rdflib import Namespace
from rdflib_endpoint import DatasetExt

ds = DatasetExt()

@ds.extension_function(namespace=Namespace("https://w3id.org/sparql-functions/"))
def split(input_str: str, separator: str = ",") -> list[str]:
    """Split a string and return each part."""
    return input_str.split(separator)
```

Example query:

```sparql
PREFIX func: <https://w3id.org/sparql-functions/>
SELECT ?input ?part WHERE {
    VALUES ?input { "hello world" "cheese is good" }
    BIND(func:split(?input, " ") AS ?part)
}
```

Use a dataclass to **populate multiple variables**, the first field of the dataclass will be returned in the bound variable, other fields will populate variables derived from the base bound variable concatenated with the fields in pascal case:

```python
from dataclasses import dataclass
from rdflib import Namespace
from rdflib_endpoint import DatasetExt

ds = DatasetExt()

@dataclass
class SplitResult:
    value: str
    index: int

@ds.extension_function(namespace=Namespace("https://w3id.org/sparql-functions/"))
def split_index(input_str: str, separator: str = ",") -> list[SplitResult]:
    """Split a string and return each part with their index."""
    return [SplitResult(value=part, index=idx) for idx, part in enumerate(input_str.split(separator))]
```

Example query:

```sparql
PREFIX func: <https://w3id.org/sparql-functions/>
SELECT ?input ?part ?partIndex WHERE {
    VALUES ?input { "hello world" "cheese is good" }
    BIND(func:splitIndex(?input, " ") AS ?part)
}
```

#### `graph_function` · Return temporary graph

Register a function that returns an `rdflib.Graph`. Use it in SPARQL as `BIND(<namespace+name>(...) AS ?g)` and then query the temporary graph with `GRAPH ?g { ... }`. Returned graphs are added to the dataset for the duration of the query and cleaned up afterwards.

```python
from rdflib import Graph, Literal, Namespace
from rdflib_endpoint import DatasetExt

ds = DatasetExt(default_union=True)
FUNC = Namespace("https://w3id.org/sparql-functions/")

@ds.graph_function(namespace=FUNC)
def split_graph(input_str: str, separator: str = ",") -> Graph:
    g = Graph()
    for part in input_str.split(separator):
        g.add((FUNC.splitting, FUNC.splitted, Literal(part)))
    return g
```

Example query:

```sparql
PREFIX func: <https://w3id.org/sparql-functions/>
SELECT * WHERE {
    VALUES ?input { "hello world" "cheese is good" }
    BIND(func:splitGraph(?input, " ") AS ?g)
    GRAPH ?g {
        ?s ?p ?o .
    }
}
```

### 📝 Define custom SPARQL functions (legacy API)

Alternatively you can manually implement evaluation extension functions by passing a `functions={...}` dict to `SparqlEndpoint` or `SparqlRouter`.

````python
import rdflib
from rdflib import Dataset
from rdflib.plugins.sparql.evalutils import _eval
from rdflib.plugins.sparql.parserutils import CompValue
from rdflib.plugins.sparql.sparql import QueryContext
from rdflib_endpoint import SparqlEndpoint

def custom_concat(query_results, ctx: QueryContext, part: CompValue, eval_part):
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
        'https://w3id.org/sparql-functions/custom_concat': custom_concat
    },
    cors_enabled=True,
    # Metadata used for the SPARQL service description and Swagger UI:
    title="SPARQL endpoint for RDFLib graph",
    description="A SPARQL endpoint to serve machine learning models, or any other logic implemented in Python. \n[Source code](https://github.com/vemonet/rdflib-endpoint)",
    version="0.1.0",
    public_url='https://your-endpoint-url/',
    # Example queries displayed in the Swagger UI to help users try your function
    example_query="""PREFIX func: <https://w3id.org/sparql-functions/>
SELECT ?concat ?concatLength WHERE {
    BIND("First" AS ?first)
    BIND(func:custom_concat(?first, "last") AS ?concat)
}"""
)
````

> [!WARNING]
> Oxigraph and `oxrdflib` do not support custom functions, so it can be only used to deploy graphs without custom functions.

### ✒️ Or directly define the custom evaluation

For full control, override the evaluation process entirely using `custom_eval`. Refer to the [RDFLib documentation](https://rdflib.readthedocs.io/en/stable/apidocs/examples.custom_eval/) for more details.

```python
import rdflib
from rdflib.plugins.sparql.evaluate import evalBGP
from rdflib.plugins.sparql.parserutils import CompValue
from rdflib.plugins.sparql.sparql import QueryContext
from rdflib.namespace import FOAF, RDF, RDFS

def custom_eval(ctx: QueryContext, part: CompValue):
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

## 📂 Projects using rdflib-endpoint

Here are some projects using `rdflib-endpoint` to deploy custom SPARQL endpoints with python:

* [The Bioregistry](https://bioregistry.io/), an open source, community curated registry, meta-registry, and compact identifier resolver.
* [proycon/codemeta-server](https://github.com/proycon/codemeta-server), server for codemeta, in memory triple store, SPARQL endpoint and simple web-based visualisation for end-user.
* [AKSW/sparql-file](https://github.com/AKSW/sparql-file), serve a RDF file as an RDFLib Graph through a SPARQL endpoint.

## 🛠️ Contributing

To run the project in development and make a contribution checkout the [contributing page](https://github.com/vemonet/rdflib-endpoint/blob/main/CONTRIBUTING.md).
