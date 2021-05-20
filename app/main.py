from typing import Optional
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse, RedirectResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware

import json
import rdflib
from rdflib.plugins.sparql.parser import Query
from rdflib.plugins.sparql.processor import translateQuery
from rdflib.plugins.sparql.results.xmlresults import XMLResult
from rdflib.plugins.sparql.results.xmlresults import XMLResultSerializer
from rdflib.namespace import Namespace
import re

from function_openpredict import SPARQL_openpredict_similarity
from openpredict_classifier import query_classifier_from_sparql

# Docs rdflib custom fct: https://rdflib.readthedocs.io/en/stable/intro_to_sparql.html
# StackOverflow: https://stackoverflow.com/questions/43976691/custom-sparql-functions-in-rdflib/66988421#66988421
# Another project: https://github.com/bas-stringer/scry/blob/master/query_handler.py
# https://www.w3.org/TR/sparql11-service-description/#example-turtle

# Federated query: https://www.w3.org/TR/2013/REC-sparql11-federated-query-20130321/#defn_service

# XML method: https://rdflib.readthedocs.io/en/stable/apidocs/rdflib.plugins.sparql.results.html#module-rdflib.plugins.sparql.results.xmlresults

app = FastAPI(
    title="SPARQL endpoint for Python functions",
    description="""A SPARQL endpoint to serve machine learning models, or any other logic implemented in Python.
    \n[Source code](https://github.com/vemonet/sparql-engine-for-python)""",
    version="0.0.1",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get(
    "/sparql",
    responses={
        200: {
            "description": "SPARQL query results",
            "content": {
                "application/sparql-results+json": {
                    "example": {"id": "bar", "value": "The bar tenders"}
                },
                "application/json": {
                    "example": {"id": "bar", "value": "The bar tenders"}
                },
                "text/csv": {
                    "example": "s,p,o"
                },
                "application/sparql-results+csv": {
                    "example": "s,p,o"
                },
                "text/turtle": {
                    "example": "service description"
                },
                "application/sparql-results+xml": {
                    "example": "<root></root>"
                },
                "application/xml": {
                    "example": "<root></root>"
                },
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
    PREFIX openpredict: <https://w3id.org/um/openpredict/>

    SELECT ?label1 ?label2 ?concat WHERE {
        BIND("Hello" AS ?label1)
        BIND("World" AS ?label2)
        BIND(openpredict:similarity(?label1, ?label2) AS ?concat)
    }
    ```
    \f
    :param query: SPARQL query input.
    """
    print('GET OPERATION. Query:')
    print(query)
    if not query:
        # Return the SPARQL endpoint service description
        service_graph = rdflib.Graph()
        # service_graph.parse('app/service-description.ttl', format="ttl")
        service_graph.parse(data=service_description_ttl, format="ttl")
        if request.headers['accept'] == 'text/turtle':
            return Response(service_graph.serialize(format = 'turtle'), media_type='text/turtle')
        else:
            return Response(service_graph.serialize(format = 'xml'), media_type='application/xml')

    # Parse the query and retrieve the type of operation (e.g. SELECT)
    parsed_query = translateQuery(Query.parseString(query, parseAll=True))
    query_operation = re.sub(r"(\w)([A-Z])", r"\1 \2", parsed_query.algebra.name)
    if query_operation != "Select Query":
        return JSONResponse(status_code=501, content={"message": str(query_operation) + " not implemented"})
    
    print(parsed_query)
    print(query_operation)
    # predictions_list = query_classifier_from_sparql(parsed_query)

    # Save custom function in custom evaluation dictionary
    rdflib.plugins.sparql.CUSTOM_EVALS['SPARQL_openpredict_similarity'] = SPARQL_openpredict_similarity

    # Query an empty graph with the custom function available
    query_results = rdflib.Graph().query(query)

    # Format and return results depending on Accept mime type in request header
    print(query_results.serialize(format = 'json'))
    output_mime_type = request.headers['accept']
    if not output_mime_type:
        output_mime_type = 'application/xml'

    print(output_mime_type)
    if output_mime_type == 'text/csv' or output_mime_type == 'application/sparql-results+csv':
        return Response(query_results.serialize(format = 'csv'), media_type=output_mime_type)
    elif output_mime_type == 'application/json' or output_mime_type == 'application/sparql-results+json':
        return Response(query_results.serialize(format = 'json'), media_type=output_mime_type)
    elif output_mime_type == 'application/xml' or output_mime_type == 'application/sparql-results+xml':
        return Response(query_results.serialize(format = 'xml'), media_type=output_mime_type)
    else:
        # By default (for federated queries)
        # return Response(query_results.serialize(format = 'sparql-results+xml'), media_type='application/sparql-results+xml')
        # return Response(XMLResultSerializer(query_results), media_type='application/sparql-results+xml')
        ## This XML serializer actually returns JSON:
        return XMLResultSerializer(query_results)

        # return FileResponse(query_results.serialize(format = 'xml'), media_type='application/sparql-results+xml', filename='sparql_results.srx')

        # return Response(json.loads(query_results.serialize(format = 'json')), media_type=output_mime_type)


from pydantic import BaseModel

class Payload(BaseModel):
    query: str = ""

@app.post(
    "/sparql",
    responses={
        200: {
            "description": "SPARQL query results",
            "content": {
                "application/sparql-results+json": {
                    "example": {"id": "bar", "value": "The bar tenders"}
                },
                "application/json": {
                    "example": {"id": "bar", "value": "The bar tenders"}
                },
                "text/csv": {
                    "example": "s,p,o"
                },
                "application/sparql-results+csv": {
                    "example": "s,p,o"
                },
                "text/turtle": {
                    "example": "service description"
                },
                "application/sparql-results+xml": {
                    "example": "<root></root>"
                },
                "application/xml": {
                    "example": "<root></root>"
                },
            },
        },
        501:{
            "description": " Not Implemented",
        }, 
    }
)
def post_sparql_endpoint(
    request: Request,
    # query: Payload = None):
    query: Optional[str] = None):
    # query: Optional[str] = Query(None)):
    # query: Optional[str] = "SELECT * WHERE { <https://identifiers.org/OMIM:246300> <https://w3id.org/biolink/vocab/treated_by> ?drug . }"):
    # def sparql_query(query: Optional[str] = None):
    """
    Send a SPARQL query to be executed through HTTP POST operation.
    \f
    :param query: SPARQL query input.
    """
    print('POST OPERATION. Query:')
    print(query)
    if not query:
        print(request)
        print("request.body:")
        print(request.body)
    return sparql_endpoint(request, query)


@app.get("/", include_in_schema=False)
async def redirect_root_to_docs():
    response = RedirectResponse(url='/docs')
    return response



service_description_ttl = """
@prefix sd: <http://www.w3.org/ns/sparql-service-description#> .
@prefix ent: <http://www.w3.org/ns/entailment/> .
@prefix prof: <http://www.w3.org/ns/owl-profile/> .
@prefix void: <http://rdfs.org/ns/void#> .

[] a sd:Service ;
    sd:endpoint <https://sparql-openpredict.137.120.31.102.nip.io/sparql> ;
    sd:supportedLanguage sd:SPARQL11Query ;
    sd:resultFormat <http://www.w3.org/ns/formats/SPARQL_Results_JSON>, <http://www.w3.org/ns/formats/SPARQL_Results_CSV> ;
    sd:extensionFunction <https://w3id.org/um/openpredict/similarity> ;
    sd:feature sd:DereferencesURIs ;
    sd:defaultEntailmentRegime ent:RDFS ;
    sd:defaultDataset [
        a sd:Dataset ;
        sd:defaultGraph [
            a sd:Graph ;
        ] 
    ] .

<https://w3id.org/um/openpredict/openpredict> a sd:Function .
"""