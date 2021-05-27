from typing import Optional
from fastapi import FastAPI, Request, Response, Body
from fastapi.responses import JSONResponse, RedirectResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware

import rdflib
from rdflib import Graph, Literal, RDF, URIRef
from rdflib.plugins.sparql.evaluate import evalPart, evalBGP
from rdflib.plugins.sparql.sparql import SPARQLError
from rdflib.plugins.sparql.evalutils import _eval
from rdflib.namespace import Namespace
from rdflib import Graph, Literal, RDF, URIRef

from rdflib.plugins.sparql.parser import Query
from rdflib.plugins.sparql.processor import translateQuery as processorTranslateQuery
from rdflib.plugins.sparql import parser
from rdflib.plugins.sparql.algebra import translateQuery, pprintAlgebra
from rdflib.plugins.sparql.results.xmlresults import XMLResult
from rdflib.plugins.sparql.results.xmlresults import XMLResultSerializer
from rdflib.namespace import Namespace
import re
from urllib import parse

from function_openpredict import SPARQL_custom_functions
from openpredict_classifier import query_openpredict_classifier
from sparql_endpoint import SparqlEndpoint

# EvalBGP https://rdflib.readthedocs.io/en/stable/_modules/rdflib/plugins/sparql/evaluate.html
# Custom fct for rdf:type with auto infer super-classes: https://github.com/RDFLib/rdflib/blob/master/examples/custom_eval.py
# BGP = Basic Graph Pattern
# Docs rdflib custom fct: https://rdflib.readthedocs.io/en/stable/intro_to_sparql.html
# StackOverflow: https://stackoverflow.com/questions/43976691/custom-sparql-functions-in-rdflib/66988421#66988421

# Another project: https://github.com/bas-stringer/scry/blob/master/query_handler.py
# https://www.w3.org/TR/sparql11-service-description/#example-turtle
# Federated query: https://www.w3.org/TR/2013/REC-sparql11-federated-query-20130321/#defn_service
# XML method: https://rdflib.readthedocs.io/en/stable/apidocs/rdflib.plugins.sparql.results.html#module-rdflib.plugins.sparql.results.xmlresults


## Suggestion to implement the package
def most_similar(query_results, ctx, part, eval_part):
    """
    Get most similar entities for a given entity
    """
    argument1 = str(_eval(part.expr.expr[0], eval_part.forget(ctx, _except=part.expr._vars)))
    argument2 = str(_eval(part.expr.expr[1], eval_part.forget(ctx, _except=part.expr._vars)))
    
    similarity_results = {}
    # TODO: get similarity from dataframe
    
    evaluation = []
    scores = []
    for most_similar in similarity_results:
        # Quick fix to get results for drugs or diseases
        # evaluation.append(most_similar['entity'])
        # scores.append(most_similar['score'])
        evaluation.append(str(argument1) + str(argument2))

    # Append the results for our custom function
    for i, result in enumerate(evaluation):
        query_results.append(eval_part.merge({
            part.var: Literal(result), 
            # rdflib.term.Variable(part.var + 'Score'): Literal(scores[i])
        }))
    return query_results, ctx, part, eval_part



def get_predictions(query_results, ctx, part, eval_part):
    """
    Query OpenPredict classifier to get drug/disease predictions
    """
    argument1 = str(_eval(part.expr.expr[0], eval_part.forget(ctx, _except=part.expr._vars)))

    # Run the classifier to get predictions and scores for the entity given as argument
    predictions_list = query_openpredict_classifier(argument1)
    evaluation = []
    scores = []
    for prediction in predictions_list:
        # Quick fix to get results for drugs or diseases
        if argument1.startswith('OMIM') or argument1.startswith('MONDO'):
            evaluation.append(prediction['drug'])
        else:
            evaluation.append(prediction['disease'])
        scores.append(prediction['score'])
    # Append the results for our custom function
    for i, result in enumerate(evaluation):
        query_results.append(eval_part.merge({
            part.var: Literal(result), 
            rdflib.term.Variable(part.var + 'Score'): Literal(scores[i])
        }))
    return query_results, ctx, part, eval_part

# Start the SPARQL endpoint based on a RDFLib Graph
g = Graph()
app = SparqlEndpoint(
    graph=g,
    functions={
        'https://w3id.org/um/openpredict/prediction': get_predictions,
        'https://w3id.org/um/openpredict/most_similar': most_similar
    })


# app = FastAPI(
#     title="SPARQL endpoint for RDFLib graph",
#     description="""A SPARQL endpoint to serve machine learning models, or any other logic implemented in Python.
#     \n[Source code](https://github.com/vemonet/rdflib-endpoint)""",
#     version="0.0.1",
# )
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )
# @app.get(
#     "/sparql",
#     responses={
#         200: {
#             "description": "SPARQL query results",
#             "content": {
#                 "application/sparql-results+json": {
#                     "example": {"id": "bar", "value": "The bar tenders"}
#                 },
#                 "application/json": {
#                     "example": {"id": "bar", "value": "The bar tenders"}
#                 },
#                 "text/csv": {
#                     "example": "s,p,o"
#                 },
#                 "application/sparql-results+csv": {
#                     "example": "s,p,o"
#                 },
#                 "text/turtle": {
#                     "example": "service description"
#                 },
#                 "application/sparql-results+xml": {
#                     "example": "<root></root>"
#                 },
#                 "application/xml": {
#                     "example": "<root></root>"
#                 },
#             },
#         },
#         501:{
#             "description": " Not Implemented",
#         }, 
#     }
# )
# def sparql_endpoint(
#     request: Request,
#     query: Optional[str] = None):
#     # query: Optional[str] = "SELECT * WHERE { <https://identifiers.org/OMIM:246300> <https://w3id.org/biolink/vocab/treated_by> ?drug . }"):
#     """
#     Send a SPARQL query to be executed. 
#     - Example with a drug: DRUGBANK:DB00394
#     - Example with a disease: OMIM:246300
#     Example with custom concat function:
#     ```
#     PREFIX openpredict: <https://w3id.org/um/openpredict/>
#     SELECT ?drugOrDisease ?predictedForTreatment ?predictedForTreatmentScore WHERE {
#         BIND("OMIM:246300" AS ?drugOrDisease)
#         BIND(openpredict:prediction(?drugOrDisease) AS ?predictedForTreatment)
#     }
#     ```
#     \f
#     :param query: SPARQL query input.
#     """
#     if not query:
#         # Return the SPARQL endpoint service description
#         service_graph = rdflib.Graph()
#         # service_graph.parse('app/service-description.ttl', format="ttl")
#         service_graph.parse(data=service_description_ttl, format="ttl")

#         # TODO: handle global registered functions
#         registered_functions = [
#             'https://w3id.org/um/openpredict/prediction',
#             'https://w3id.org/um/openpredict/most_similar'
#         ]
#         for custom_function in registered_functions:
#             service_graph.add(URIRef(custom_function), RDF.type, URIRef('http://www.w3.org/ns/sparql-service-description#Function'))

#         # Return the service description RDF as turtle or XML
#         if request.headers['accept'] == 'text/turtle':
#             return Response(service_graph.serialize(format = 'turtle'), media_type='text/turtle')
#         else:
#             return Response(service_graph.serialize(format = 'xml'), media_type='application/xml')

#     # Parse the query and retrieve the type of operation (e.g. SELECT)
#     parsed_query = processorTranslateQuery(Query.parseString(query, parseAll=True))
#     query_operation = re.sub(r"(\w)([A-Z])", r"\1 \2", parsed_query.algebra.name)
#     if query_operation != "Select Query":
#         return JSONResponse(status_code=501, content={"message": str(query_operation) + " not implemented"})
    
#     # Pretty print the query object 
#     parsed_query = parser.parseQuery(query)
#     tq = translateQuery(parsed_query)
#     pprintAlgebra(tq)

#     # Save custom function in custom evaluation dictionary
#     # Handle multiple functions directly in the SPARQL_custom_functions function
#     rdflib.plugins.sparql.CUSTOM_EVALS['SPARQL_custom_functions'] = SPARQL_custom_functions

#     # Query an empty graph with the custom functions loaded
#     query_results = rdflib.Graph().query(query)

#     # Format and return results depending on Accept mime type in request header
#     output_mime_type = request.headers['accept']
#     if not output_mime_type:
#         output_mime_type = 'application/xml'

#     # print(output_mime_type)
#     if output_mime_type == 'text/csv' or output_mime_type == 'application/sparql-results+csv':
#         return Response(query_results.serialize(format = 'csv'), media_type=output_mime_type)
#     elif output_mime_type == 'application/json' or output_mime_type == 'application/sparql-results+json':
#         return Response(query_results.serialize(format = 'json'), media_type=output_mime_type)
#     elif output_mime_type == 'application/xml' or output_mime_type == 'application/sparql-results+xml':
#         return Response(query_results.serialize(format = 'xml'), media_type=output_mime_type)
#     else:
#         ## By default (for federated queries)
#         return Response(query_results.serialize(format = 'xml'), media_type='application/sparql-results+xml')

# @app.post(
#     "/sparql",
#     responses={
#         200: {
#             "description": "SPARQL query results",
#             "content": {
#                 "application/sparql-results+json": {
#                     "example": {"id": "bar", "value": "The bar tenders"}
#                 },
#                 "application/json": {
#                     "example": {"id": "bar", "value": "The bar tenders"}
#                 },
#                 "text/csv": {
#                     "example": "s,p,o"
#                 },
#                 "application/sparql-results+csv": {
#                     "example": "s,p,o"
#                 },
#                 "text/turtle": {
#                     "example": "service description"
#                 },
#                 "application/sparql-results+xml": {
#                     "example": "<root></root>"
#                 },
#                 "application/xml": {
#                     "example": "<root></root>"
#                 },
#             },
#         },
#         501:{
#             "description": " Not Implemented",
#         }, 
#     }
# )
# async def post_sparql_endpoint(
#     request: Request,
#     query: Optional[str] = None):
#     """
#     Send a SPARQL query to be executed through HTTP POST operation.
#     \f
#     :param query: SPARQL query input.
#     """
#     if not query:
#         # Handle federated query services which provide the query in the body
#         query_body = await request.body()
#         body = parse.unquote(query_body.decode('utf-8'))
#         parsed_query = parse.parse_qsl(body)
#         for params in parsed_query:
#             if params[0] == 'query':
#                 query = params[1]
#     return sparql_endpoint(request, query)


# @app.get("/", include_in_schema=False)
# async def redirect_root_to_docs():
#     response = RedirectResponse(url='/docs')
#     return response


# # Service description returned when no query provided
# service_description_ttl = """
# @prefix sd: <http://www.w3.org/ns/sparql-service-description#> .
# @prefix ent: <http://www.w3.org/ns/entailment/> .
# @prefix prof: <http://www.w3.org/ns/owl-profile/> .
# @prefix void: <http://rdfs.org/ns/void#> .

# [] a sd:Service ;
#     sd:endpoint <https://sparql-openpredict.137.120.31.102.nip.io/sparql> ;
#     sd:supportedLanguage sd:SPARQL11Query ;
#     sd:resultFormat <http://www.w3.org/ns/formats/SPARQL_Results_JSON>, <http://www.w3.org/ns/formats/SPARQL_Results_CSV> ;
#     sd:extensionFunction <https://w3id.org/um/openpredict/similarity> ;
#     sd:feature sd:DereferencesURIs ;
#     sd:defaultEntailmentRegime ent:RDFS ;
#     sd:defaultDataset [
#         a sd:Dataset ;
#         sd:defaultGraph [
#             a sd:Graph ;
#         ] 
#     ] .
# """