# ✨ SPARQL endpoint for RDFLib

[![Version](https://img.shields.io/pypi/v/rdflib-endpoint)](https://pypi.org/project/rdflib-endpoint) [![Python versions](https://img.shields.io/pypi/pyversions/rdflib-endpoint)](https://pypi.org/project/rdflib-endpoint)

[![Run tests](https://github.com/vemonet/rdflib-endpoint/actions/workflows/run-tests.yml/badge.svg)](https://github.com/vemonet/rdflib-endpoint/actions/workflows/run-tests.yml) [![Publish to PyPI](https://github.com/vemonet/rdflib-endpoint/actions/workflows/publish-package.yml/badge.svg)](https://github.com/vemonet/rdflib-endpoint/actions/workflows/publish-package.yml) [![CodeQL](https://github.com/vemonet/rdflib-endpoint/actions/workflows/codeql-analysis.yml/badge.svg)](https://github.com/vemonet/rdflib-endpoint/actions/workflows/codeql-analysis.yml) [![Coverage](https://sonarcloud.io/api/project_badges/measure?project=vemonet_rdflib-endpoint&metric=coverage)](https://sonarcloud.io/dashboard?id=vemonet_rdflib-endpoint)

`rdflib-endpoint` is a SPARQL endpoint based on RDFLib to easily serve RDF files, machine learning models, or any other logic implemented in Python via **custom SPARQL functions**. 

It aims to enable python developers to easily deploy functions that can be queried in a federated fashion using SPARQL. For example: using a python function to resolve labels for specific identifiers, or run a classifier given entities retrieved using a `SERVICE` query to another SPARQL endpoint.

> Feel free to create an [issue](/issues), or send a pull request if you are facing issues or would like to see a feature implemented.

## 🧑‍🏫 How it works

The user defines and registers custom SPARQL functions using Python, and/or populate the RDFLib Graph, then the endpoint is started using `uvicorn`. 

The deployed SPARQL endpoint can be used as a `SERVICE` in a federated SPARQL query from regular triplestores SPARQL endpoints. Tested on OpenLink Virtuoso (Jena based) and Ontotext GraphDB (rdf4j based). The endpoint is CORS enabled by default.

`rdflib-endpoint` can also be used directly from the terminal to quickly serve a RDF file as a SPARQL endpoint.

Built with [RDFLib](https://github.com/RDFLib/rdflib) and [FastAPI](https://fastapi.tiangolo.com/). Tested for Python 3.7, 3.8 and 3.9

## 📥 Install the package

Install the package from [PyPI](https://pypi.org/project/rdflib-endpoint/):

```bash
pip install rdflib-endpoint
```

## ⚡️ Quickly serve RDF files via a SPARQL endpoint

Use `rdflib-endpoint` as a command line interface (CLI) in your terminal to quickly serve one or multiple RDF files as a SPARQL endpoint, with YASGUI interface available on http://0.0.0.0:8000

You can use wildcard and provide multiple files, for example to serve all turtle, JSON-LD and nquads files in the current folder:

```bash
rdflib-endpoint serve *.ttl *.jsonld *.nq
```

## 🐍 SPARQL endpoint with custom functions

Checkout the [`example`](https://github.com/vemonet/rdflib-endpoint/tree/main/example) folder for a complete working app example to get started, including a docker deployment. A good way to create a new SPARQL endpoint is to copy this `example` folder, and start from it.

### 📝 Define custom SPARQL functions

This option makes it easier to define functions in your SPARQL endpoint, e.g. `BIND(myfunction:custom_concat("start", "end") AS ?concat)`

Create a `app/main.py` file in your project folder with your custom SPARQL functions, and endpoint parameters:

````python
from rdflib_endpoint import SparqlEndpoint
import rdflib
from rdflib.plugins.sparql.evalutils import _eval

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
g = rdflib.graph.ConjunctiveGraph()
app = SparqlEndpoint(
    graph=g,
    # Register the functions:
    functions={
        'https://w3id.org/um/sparql-functions/custom_concat': custom_concat
    },
    cors_enabled=True,
    # Metadata used for the SPARQL service description and Swagger UI:
    title="SPARQL endpoint for RDFLib graph", 
    description="A SPARQL endpoint to serve machine learning models, or any other logic implemented in Python. \n[Source code](https://github.com/vemonet/rdflib-endpoint)",
    version="0.1.0",
    public_url='https://your-endpoint-url/sparql',
    # Example queries displayed in the Swagger UI to help users try your function
    example_query="""Example query:\n
```
PREFIX myfunctions: <https://w3id.org/um/sparql-functions/>
SELECT ?concat ?concatLength WHERE {
    BIND("First" AS ?first)
    BIND(myfunctions:custom_concat(?first, "last") AS ?concat)
}
```"""
)
````

### 📝 Or directly define the custom evaluation

You can also directly provide the custom evaluation function, this will override the `functions`.

Refer to the [RDFLib documentation](https://rdflib.readthedocs.io/en/stable/_modules/examples/custom_eval.html) to define the custom evaluation function. Then provide it when instantiating the SPARQL endpoint:

```python
import rdflib
from rdflib.plugins.sparql.evaluate import evalBGP
from rdflib.namespace import FOAF, RDF, RDFS

def customEval(ctx, part):
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
    custom_eval=customEval
)
```

### 🦄 Run the SPARQL endpoint

You can then run the SPARQL endpoint server from the `example` folder on http://localhost:8000/sparql with `uvicorn`

```bash
cd example
uvicorn main:app --app-dir app --reload
```

You can access the YASGUI interface to easily query the SPARQL endpoint on http://localhost:8000

> Checkout in the `example/README.md` for more details, such as deploying it with docker.

## 🧑‍💻 Development

### 📥 Install for development

Install from the latest GitHub commit to make sure you have the latest updates:

```bash
pip install rdflib-endpoint@git+https://github.com/vemonet/rdflib-endpoint@main
```

Or clone and install locally for development:

```bash
git clone https://github.com/vemonet/rdflib-endpoint
cd rdflib-endpoint
pip install -e .
```

You can use a virtual environment to avoid conflicts:

```bash
# Create the virtual environment folder in your workspace
python3 -m venv .venv
# Activate it using a script in the created folder
source .venv/bin/activate
```

### ✅️ Run the tests

Install additional dependencies for testing:

```bash
pip install pytest requests
```

Run the tests locally (from the root folder) and display prints:

```bash
pytest -s
```

## 📂 Projects using rdflib-endpoint

Here are some projects using `rdflib-endpoint` to deploy custom SPARQL endpoints with python:

* https://github.com/MaastrichtU-IDS/rdflib-endpoint-sparql-service
  * Serve predicted biomedical entities associations (e.g. disease treated by drug) using the rdflib-endpoint classifier
* https://github.com/vemonet/translator-sparql-service
  * A SPARQL endpoint to serve NCATS Translator services as SPARQL custom functions.
