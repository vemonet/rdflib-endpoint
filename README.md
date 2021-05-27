# SPARQL endpoint for RDFLib custom functions ✨️

[![Run tests](https://github.com/vemonet/rdflib-endpoint/actions/workflows/run-tests.yml/badge.svg)](https://github.com/vemonet/rdflib-endpoint/actions/workflows/run-tests.yml)[![CodeQL](https://github.com/vemonet/rdflib-endpoint/actions/workflows/codeql-analysis.yml/badge.svg)](https://github.com/vemonet/rdflib-endpoint/actions/workflows/codeql-analysis.yml)

A SPARQL endpoint to serve machine learning models, or any other logic implemented in Python.

Built with [RDFLib](https://github.com/RDFLib/rdflib) and [FastAPI](https://fastapi.tiangolo.com/), CORS enabled.

Tested for python 3.6 to 3.9.

## Install 📥

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

## Define custom functions 🐍

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

# Start the SPARQL endpoint based on a RDFLib Graph
g = rdflib.Graph()
app = SparqlEndpoint(
    graph=g,
    functions={
        'https://w3id.org/um/sparql-functions/custom_concat': custom_concat
    },
    title="SPARQL endpoint for RDFLib graph", 
    description="A SPARQL endpoint to serve machine learning models, or any other logic implemented in Python. \n[Source code](https://github.com/vemonet/rdflib-endpoint)",
    version="0.0.1",
    cors_enabled=True
)
```

Checkout the `example/` folder for a complete working app example (with docker-compose based deployment)

## Run the endpoint 🦄

Run the FastAPI server from the root folder with `uvicorn` on http://localhost:8000 

```bash
uvicorn main:app --reload --app-dir app
```

