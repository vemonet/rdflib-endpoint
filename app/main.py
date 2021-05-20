from typing import Optional
from fastapi import FastAPI, Request, Response, Query
from fastapi.responses import JSONResponse, RedirectResponse, PlainTextResponse

import json
import rdflib
from rdflib.plugins.sparql.parser import Query
from rdflib.plugins.sparql.processor import translateQuery
from rdflib.namespace import Namespace
import re

from function_openpredict import SPARQL_openpredict
from openpredict_classifier import query_classifier_from_sparql

# Docs rdflib custom fct: https://rdflib.readthedocs.io/en/stable/intro_to_sparql.html
# StackOverflow: https://stackoverflow.com/questions/43976691/custom-sparql-functions-in-rdflib/66988421#66988421
# Another project: https://github.com/bas-stringer/scry/blob/master/query_handler.py

app = FastAPI(
    title="SPARQL endpoint for Python functions",
    description="""A SPARQL endpoint to serve machine learning models, or any other logic implemented in Python.
    \n[Source code](https://github.com/vemonet/sparql-engine-for-python)""",
    version="0.0.1",
)

@app.get(
    "/sparql",
    responses={
        200: {
            "description": "SPARQL query results",
            "content": {
                "application/json": {
                    "example": {"id": "bar", "value": "The bar tenders"}
                },
                "text/csv": {
                    "example": "s,p,o"
                }
            },
        },
        501:{
            "description": " Not Implemented",
        }, 
    }
)
def sparql_endpoint(
    request: Request,
    query: Optional[str] = None):
    # query: Optional[str] = Query(None)):
    # query: Optional[str] = "SELECT * WHERE { <https://identifiers.org/OMIM:246300> <https://w3id.org/biolink/vocab/treated_by> ?drug . }"):
    # def sparql_query(query: Optional[str] = None):
    """
    Send a SPARQL query to be executed. 
    - Example with a drug: https://identifiers.org/DRUGBANK:DB00394
    - Example with a disease: https://identifiers.org/OMIM:246300
    Example with custom concat function:
    ```
    PREFIX custom: <//custom/>

    SELECT ?label1 ?label2 ?concat WHERE {
        BIND("Hello" AS ?label1)
        BIND("World" AS ?label2)
        BIND(custom:openpredict(?label1, ?label2) AS ?concat)
    }
    ```
    \f
    :param query: SPARQL query input.
    """
    if not query:
        # Return the SPARQL endpoint service description
        service_graph = rdflib.Graph()
        service_graph.parse('app/service-description.ttl', format="ttl")
        if request.headers['accept'] == 'application/xml':
            return Response(service_graph.serialize(format = 'xml'), media_type='application/xml')
        else:
            return Response(service_graph.serialize(format = 'turtle'), media_type='text/turtle')

    # Parse the query and retrieve the type of operation (e.g. SELECT)
    parsed_query = translateQuery(Query.parseString(query, parseAll=True))
    query_operation = re.sub(r"(\w)([A-Z])", r"\1 \2", parsed_query.algebra.name)
    if query_operation != "Select Query":
        return JSONResponse(status_code=501, content={"message": str(query_operation) + " not implemented"})
    
    print(parsed_query)
    print(query_operation)
    # predictions_list = query_classifier_from_sparql(parsed_query)

    # Save custom function in custom evaluation dictionary.
    rdflib.plugins.sparql.CUSTOM_EVALS['SPARQL_openpredict'] = SPARQL_openpredict

    # Query an empty graph with the custom function available
    query_results = rdflib.Graph().query(query)

    # Format and return results
    print(query_results.serialize(format = 'json'))
    if request.headers['accept'] == 'text/csv':
        return Response(query_results.serialize(format = 'csv'), media_type='text/csv')
    else:
        return json.loads(query_results.serialize(format = 'json'))


@app.get("/", include_in_schema=False)
async def redirect_root_to_docs():
    response = RedirectResponse(url='/docs')
    return response

# https://www.w3.org/TR/sparql11-service-description/#example-turtle
sparql_service_description = """
@prefix sd: <http://www.w3.org/ns/sparql-service-description#> .
@prefix ent: <http://www.w3.org/ns/entailment/> .
@prefix prof: <http://www.w3.org/ns/owl-profile/> .
@prefix void: <http://rdfs.org/ns/void#> .

[] a sd:Service ;
    sd:endpoint <https://sparql-openpredict.137.120.31.102.nip.io/sparql> ;
    sd:supportedLanguage sd:SPARQL11Query ;
    sd:resultFormat <http://www.w3.org/ns/formats/SPARQL_Results_JSON>, <http://www.w3.org/ns/formats/SPARQL_Results_CSV> ;
    sd:extensionFunction <//custom/openpredict> ;
    sd:feature sd:DereferencesURIs ;
    sd:defaultEntailmentRegime ent:RDFS ;
    sd:defaultDataset [
        a sd:Dataset ;
        sd:defaultGraph [
            a sd:Graph ;
        ] 
    ] .

<//custom/openpredict> a sd:Function .
"""