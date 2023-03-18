<div align="center">

# 💫 SPARQL endpoint for RDFLib

[![PyPI - Version](https://img.shields.io/pypi/v/rdflib-endpoint.svg?logo=pypi&label=PyPI&logoColor=silver)](https://pypi.org/project/rdflib-endpoint/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/rdflib-endpoint.svg?logo=python&label=Python&logoColor=silver)](https://pypi.org/project/rdflib-endpoint/)

[![Test package](https://github.com/vemonet/rdflib-endpoint/actions/workflows/test.yml/badge.svg)](https://github.com/vemonet/rdflib-endpoint/actions/workflows/test.yml)
[![Publish package](https://github.com/vemonet/rdflib-endpoint/actions/workflows/publish.yml/badge.svg)](https://github.com/vemonet/rdflib-endpoint/actions/workflows/publish.yml)
[![Test coverage](https://sonarcloud.io/api/project_badges/measure?project=vemonet_rdflib-endpoint&metric=coverage)](https://sonarcloud.io/dashboard?id=vemonet_rdflib-endpoint)

[![license](https://img.shields.io/pypi/l/rdflib-endpoint.svg?color=%2334D058)](https://github.com/vemonet/rdflib-endpoint/blob/main/LICENSE.txt)
[![code style - black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![types - Mypy](https://img.shields.io/badge/types-mypy-blue.svg)](https://github.com/python/mypy)

</div>

`rdflib-endpoint` is a SPARQL endpoint based on RDFLib to **easily serve RDF files locally**, machine learning models, or any other logic implemented in Python via **custom SPARQL functions**.

It aims to enable python developers to easily deploy functions that can be queried in a federated fashion using SPARQL. For example: using a python function to resolve labels for specific identifiers, or run a classifier given entities retrieved using a `SERVICE` query to another SPARQL endpoint.

> Feel free to create an [issue](/issues), or send a pull request if you are facing issues or would like to see a feature implemented.

## ℹ️ How it works

`rdflib-endpoint` can be used directly from the terminal to quickly serve RDF files through a SPARQL endpoint automatically deployed locally.

It can also be used to define custom SPARQL functions: the user defines and registers custom SPARQL functions, and/or populate the RDFLib Graph using Python, then the endpoint is started using `uvicorn`/`gunicorn`.

The deployed SPARQL endpoint can be used as a `SERVICE` in a federated SPARQL query from regular triplestores SPARQL endpoints. Tested on OpenLink Virtuoso (Jena based) and Ontotext GraphDB (rdf4j based). The endpoint is CORS enabled by default.

Built with [RDFLib](https://github.com/RDFLib/rdflib) and [FastAPI](https://fastapi.tiangolo.com/).

## 📦️ Installation

This package requires Python >=3.7, simply install it  from [PyPI](https://pypi.org/project/rdflib-endpoint/) with:

```shell
pip install rdflib-endpoint
```

If you want to use [oxigraph](https://github.com/oxigraph/oxigraph) as backend triplestore you can install with the optional dependency:

```bash
pip install "rdflib-endpoint[oxigraph]"
```

> ⚠️ Oxigraph and `oxrdflib` do not support custom functions, so it can be only used to deploy graphs without custom functions.

## ⚡️ Quickly serve RDF files via a SPARQL endpoint

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
    path="/",
    public_url='https://your-endpoint-url/',
    # Example queries displayed in the Swagger UI to help users try your function
    example_query="""PREFIX myfunctions: <https://w3id.org/um/sparql-functions/>
SELECT ?concat ?concatLength WHERE {
    BIND("First" AS ?first)
    BIND(myfunctions:custom_concat(?first, "last") AS ?concat)
}"""
)
````

### 📝 Or directly define the custom evaluation

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

You can then run the SPARQL endpoint server from the folder where your script is defined with `uvicorn` on http://localhost:8000/sparql (which is installed automatically when you install the `rdflib-endpoint` package)

```bash
uvicorn main:app --app-dir app --reload
```

You can access the YASGUI interface to easily query the SPARQL endpoint on http://localhost:8000

> Checkout in the `example/README.md` for more details, such as deploying it with docker.

## 🧑‍💻 Development

This section is for if you want to run the package in development, and get involved by making a code contribution.

### 📥️ Clone

Clone the repository:

```bash
git clone https://github.com/vemonet/rdflib-endpoint
cd rdflib-endpoint
```

### 🐣 Install dependencies

Install [Hatch](https://hatch.pypa.io), this will automatically handle virtual environments and make sure all dependencies are installed when you run a script in the project:

```bash
pip install --upgrade hatch
```

Install the dependencies in a local virtual environment (running this command is optional as `hatch` will automatically install and synchronize dependencies each time you run a script with `hatch run`):

```bash
hatch -v env create
```

### 🚀 Run example API

The API will be automatically reloaded when the code is changed:

```bash
hatch run dev
```

Access the YASGUI interface at http://localhost:8000

Or query directly the SPARQL endpoint at http://localhost:8000/sparql

### ☑️ Run tests

Make sure the existing tests still work by running ``pytest``. Note that any pull requests to the fairworkflows repository on github will automatically trigger running of the test suite;

```bash
hatch run test
```

To display all `print()`:

```bash
hatch run test -s
```

### 🧹 Code formatting

The code will be automatically formatted when you commit your changes using `pre-commit`. But you can also run the script to format the code yourself:

```
hatch run fmt
```

Check the code for errors, and if it is in accordance with the PEP8 style guide, by running `ruff` and `mypy`:

```
hatch run check
```

### ♻️ Reset the environment

In case you are facing issues with dependencies not updating properly you can easily reset the virtual environment with:

```bash
hatch env prune
```

### 🏷️ New release process

The deployment of new releases is done automatically by a GitHub Action workflow when a new release is created on GitHub. To release a new version:

1. Make sure the `PYPI_TOKEN` secret has been defined in the GitHub repository (in Settings > Secrets > Actions). You can get an API token from PyPI at [pypi.org/manage/account](https://pypi.org/manage/account).

2. Increment the `version` number following semantic versioning, select between `fix`, `minor`, or `major`:

   ```bash
   hatch version fix
   ```

3. Create a new release on GitHub, which will automatically trigger the publish workflow, and publish the new release to PyPI.

You can also manually trigger the workflow from the Actions tab in your GitHub repository webpage if needed.

## 📂 Projects using rdflib-endpoint

Here are some projects using `rdflib-endpoint` to deploy custom SPARQL endpoints with python:

* [MaastrichtU-IDS/rdflib-endpoint-sparql-service](https://github.com/MaastrichtU-IDS/rdflib-endpoint-sparql-service)
  * Serve predicted biomedical entities associations (e.g. disease treated by drug) using the rdflib-endpoint classifier
* [vemonet/translator-sparql-service](https://github.com/vemonet/translator-sparql-service)
  * A SPARQL endpoint to serve NCATS Translator services as SPARQL custom functions.
* [proycon/codemeta-server](https://github.com/proycon/codemeta-server)
  * Server for codemeta, in memory triple store, SPARQL endpoint and simple web-based visualisation for end-user
