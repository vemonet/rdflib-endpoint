import rdflib
from rdflib import Graph
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

from typing import Optional
from fastapi import FastAPI, Request, Response, Body
from fastapi.responses import JSONResponse, RedirectResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware

from fastapi import FastAPI
# from fastapi_utils.cbv import cbv
# from fastapi_utils.inferring_router import InferringRouter

# from openpredict_classifier import query_openpredict_classifier

class SparqlEndpoint(FastAPI):
    """
    Class to deploy a SPARQL endpoint using a RDFLib Graph
    """

    def __init__(self, 
            title: str = "SPARQL endpoint for RDFLib graph", 
            description="A SPARQL endpoint to serve machine learning models, or any other logic implemented in Python. \n[Source code](https://github.com/vemonet/rdflib-endpoint)",
            version="0.0.1",
            graph=Graph(), 
            functions={},
            cors_enabled=True) -> None:
        self.graph = graph
        self.functions = functions
        # Instantiate FastAPI
        super().__init__(title=title, description=description, version=version)
        
        if cors_enabled:
            self.add_middleware(
                CORSMiddleware,
                allow_origins=["*"],
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )

        @self.get(
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
        def sparql_endpoint(request: Request,
            query: Optional[str] = None):
            # query: Optional[str] = "SELECT * WHERE { <https://identifiers.org/OMIM:246300> <https://w3id.org/biolink/vocab/treated_by> ?drug . }"):
            """
            Send a SPARQL query to be executed. 
            - Example with a drug: DRUGBANK:DB00394
            - Example with a disease: OMIM:246300
            Example with custom concat function:
            ```
            PREFIX myfunctions: <https://w3id.org/um/sparql-functions/>
            SELECT ?concat ?concatLength WHERE {
                BIND("First" AS ?first)
                BIND(myfunctions:custom_concat(?first, "last") AS ?concat)
            }
            ```
            Example with custom function to get predictions from a classifier (works also with drugs, e.g. DRUGBANK:DB00394):
            ```
            PREFIX openpredict: <https://w3id.org/um/openpredict/>
            SELECT ?drugOrDisease ?predictedForTreatment ?predictedForTreatmentScore WHERE {
                BIND("OMIM:246300" AS ?drugOrDisease)
                BIND(openpredict:prediction(?drugOrDisease) AS ?predictedForTreatment)
            }
            ```
            \f
            :param query: SPARQL query input.
            """
            if not query:
                # Return the SPARQL endpoint service description
                service_graph = rdflib.Graph()
                # service_graph.parse('app/service-description.ttl', format="ttl")
                service_graph.parse(data=service_description_ttl, format="ttl")

                for custom_function in self.functions.keys():
                    service_graph.add((URIRef(custom_function), RDF.type, URIRef('http://www.w3.org/ns/sparql-service-description#Function')))

                # Return the service description RDF as turtle or XML
                if request.headers['accept'] == 'text/turtle':
                    return Response(service_graph.serialize(format = 'turtle'), media_type='text/turtle')
                else:
                    return Response(service_graph.serialize(format = 'xml'), media_type='application/xml')

            # Parse the query and retrieve the type of operation (e.g. SELECT)
            parsed_query = processorTranslateQuery(Query.parseString(query, parseAll=True))
            query_operation = re.sub(r"(\w)([A-Z])", r"\1 \2", parsed_query.algebra.name)
            if query_operation != "Select Query":
                return JSONResponse(status_code=501, content={"message": str(query_operation) + " not implemented"})
            
            # Pretty print the query object 
            parsed_query = parser.parseQuery(query)
            tq = translateQuery(parsed_query)
            pprintAlgebra(tq)

            # Save custom function in custom evaluation dictionary
            # Handle multiple functions directly in the SPARQL_custom_functions function
            rdflib.plugins.sparql.CUSTOM_EVALS['SPARQL_custom_functions'] = SPARQL_custom_functions

            # Query an empty graph with the custom functions loaded
            query_results = rdflib.Graph().query(query)

            # Format and return results depending on Accept mime type in request header
            output_mime_type = request.headers['accept']
            if not output_mime_type:
                output_mime_type = 'application/xml'

            # print(output_mime_type)
            if output_mime_type == 'text/csv' or output_mime_type == 'application/sparql-results+csv':
                return Response(query_results.serialize(format = 'csv'), media_type=output_mime_type)
            elif output_mime_type == 'application/json' or output_mime_type == 'application/sparql-results+json':
                return Response(query_results.serialize(format = 'json'), media_type=output_mime_type)
            elif output_mime_type == 'application/xml' or output_mime_type == 'application/sparql-results+xml':
                return Response(query_results.serialize(format = 'xml'), media_type=output_mime_type)
            else:
                ## By default (for federated queries)
                return Response(query_results.serialize(format = 'xml'), media_type='application/sparql-results+xml')

        @self.post(
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
        async def post_sparql_endpoint(
            request: Request,
            query: Optional[str] = None):
            """
            Send a SPARQL query to be executed through HTTP POST operation.
            \f
            :param query: SPARQL query input.
            """
            if not query:
                # Handle federated query services which provide the query in the body
                query_body = await request.body()
                body = parse.unquote(query_body.decode('utf-8'))
                parsed_query = parse.parse_qsl(body)
                for params in parsed_query:
                    if params[0] == 'query':
                        query = params[1]
            return sparql_endpoint(request, query)


        def SPARQL_custom_functions(ctx:object, part:object) -> object:
            """
            Retrieve variables from a SPARQL-query, then get predictions
            The score value is then stored in Literal object and added to the query results.
            
            Example:

            Query:
                PREFIX openpredict: <https://w3id.org/um/openpredict/>
                SELECT ?drugOrDisease ?predictedForTreatment ?predictedForTreatmentScore WHERE {
                    BIND("OMIM:246300" AS ?drugOrDisease)
                    BIND(openpredict:prediction(?drugOrDisease) AS ?predictedForTreatment)
                }

                BIND(openpredict:score(?drugOrDisease) AS ?predictedForTreatment)
                https://github.com/w3c/sparql-12/issues/6

            Problem with this query: how to retrieve the ?score ? We just add it to the results?

            Retrieve:
                ?label1 ?label2

            Calculation:
                prediction(?label1, ?label2) =  score

            Output:
                Save score in Literal object.

            :param ctx:     <class 'rdflib.plugins.sparql.sparql.QueryContext'>
            :param part:    <class 'rdflib.plugins.sparql.parserutils.CompValue'>
            :return:        <class 'rdflib.plugins.sparql.processor.SPARQLResult'>
            """

            # This part holds basic implementation for adding new functions
            if part.name == 'Extend':
                query_results = []

                # Information is retrieved and stored and passed through a generator
                for eval_part in evalPart(ctx, part.p):
                    # Checks if the function is a URI (custom function)
                    if hasattr(part.expr, 'iri'):

                        # Execute custom functions passed in the constructor
                        for function_uri, custom_function in self.functions.items():
                            if part.expr.iri == URIRef(function_uri):
                                query_results, ctx, part, eval_part = custom_function(query_results, ctx, part, eval_part)

                    else:
                        # For built-in SPARQL functions (that are not URIs)
                        evaluation = [_eval(part.expr, eval_part.forget(ctx, _except=part._vars))]
                        if isinstance(evaluation[0], SPARQLError):
                            raise evaluation[0]
                        # Append results for built-in SPARQL functions
                        for result in evaluation:
                            query_results.append(eval_part.merge({part.var: Literal(result)}))
                            
                # print(query_results)
                return query_results
            raise NotImplementedError()


        @self.get("/", include_in_schema=False)
        async def redirect_root_to_docs():
            response = RedirectResponse(url='/docs')
            return response


        # Service description returned when no query provided
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
        """