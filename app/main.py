from typing import Optional
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse, RedirectResponse, PlainTextResponse

import rdflib
from rdflib.plugins.sparql.parser import Query
from rdflib.plugins.sparql.processor import translateQuery
from rdflib.namespace import Namespace
import re

from function_openpredict import SPARQL_openpredict
from openpredict_classifier import query_classifier_from_sparql

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
    query: Optional[str] = "SELECT * WHERE { <https://identifiers.org/OMIM:246300> <https://w3id.org/biolink/vocab/treated_by> ?drug . }"):
    # def sparql_query(query: Optional[str] = None):
    """
    Send a SPARQL query to be executed. 
    - Example with a drug: https://identifiers.org/DRUGBANK:DB00394
    - Example with a disease: https://identifiers.org/OMIM:246300
    \f
    :param query: SPARQL query input.
    """
    if not query:
        # TODO: return the SPARQL enndpoint service description
        return {"SPARQL Service": "description"}
    
    if request.headers['accept'] == 'text/csv':
        # TODO: return in CSV format
        return Response('a,b,c', media_type='text/csv')
    else:
        parsed_query = translateQuery(Query.parseString(query, parseAll=True))
        query_operation = re.sub(r"(\w)([A-Z])", r"\1 \2", parsed_query.algebra.name)
        if query_operation != "Select Query":
            return JSONResponse(status_code=501, content={"message": str(query_operation) + " not implemented"})
        
        print(parsed_query)
        print(query_operation)
        # predictions_list = query_classifier_from_sparql(parsed_query)
        
        # Docs rdflib custom fct: https://rdflib.readthedocs.io/en/stable/intro_to_sparql.html
        # StackOverflow: https://stackoverflow.com/questions/43976691/custom-sparql-functions-in-rdflib/66988421#66988421
        # Another project: https://github.com/bas-stringer/scry/blob/master/query_handler.py


        # Save custom function in custom evaluation dictionary.
        rdflib.plugins.sparql.CUSTOM_EVALS['SPARQL_openpredict'] = SPARQL_openpredict
        predictions_list = []
        for row in rdflib.Graph().query(query):
            predictions_list.append(row)

        return predictions_list


@app.get("/", include_in_schema=False)
async def redirect_root_to_docs():
    response = RedirectResponse(url='/docs')
    return response

