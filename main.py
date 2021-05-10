from typing import Optional
from fastapi import FastAPI, Request, Response
from starlette.responses import PlainTextResponse, RedirectResponse

from rdflib.plugins.sparql.parser import Query
from rdflib.plugins.sparql.processor import translateQuery

app = FastAPI(
    title="SPARQL query engine for ML model",
    description="A SPARQL endpoint to serve machine learning models, or any other logic implemented in Python",
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
    },
)
def sparql_query(
    request: Request,
    query: Optional[str] = "SELECT * WHERE { ?s a <http://test> ; ?p ?o . }"):
    # def sparql_query(query: Optional[str] = None):
    """
    Send a SPARQL query to be executed
    \f
    :param query: SPARQL query input.
    """
    print(request.headers['accept'])
    if not query:
        return {"SPARQL Service": "description"}
    
    if request.headers['accept'] == 'text/csv':
        return Response('a,b,c', media_type='text/csv')
    else:
        query = str(query)
        parsed_query = translateQuery(Query.parseString(query, parseAll=True))
        return parsed_query


@app.get("/", include_in_schema=False)
async def redirect_root_to_docs():
    response = RedirectResponse(url='/docs')
    return response

