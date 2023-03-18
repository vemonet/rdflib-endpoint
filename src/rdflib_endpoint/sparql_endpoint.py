import logging
import re
import time
from typing import Any, Callable, Dict, List, Optional, Union
from urllib import parse

import pkg_resources
import rdflib
from fastapi import FastAPI, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from rdflib import RDF, ConjunctiveGraph, Dataset, Graph, Literal, URIRef
from rdflib.plugins.sparql import prepareQuery
from rdflib.plugins.sparql.evaluate import evalPart
from rdflib.plugins.sparql.evalutils import _eval
from rdflib.plugins.sparql.parserutils import CompValue
from rdflib.plugins.sparql.sparql import QueryContext, SPARQLError

__all__ = [
    "SparqlEndpoint",
]


EXAMPLE_SPARQL = """\
PREFIX myfunctions: <https://w3id.org/um/sparql-functions/>

SELECT ?concat ?concatLength WHERE {
    BIND("First" AS ?first)
    BIND(myfunctions:custom_concat(?first, "last") AS ?concat)
}
""".rstrip()

SERVICE_DESCRIPTION_TTL_FMT = """\
@prefix sd: <http://www.w3.org/ns/sparql-service-description#> .
@prefix ent: <http://www.w3.org/ns/entailment/> .
@prefix prof: <http://www.w3.org/ns/owl-profile/> .
@prefix void: <http://rdfs.org/ns/void#> .
@prefix dc: <http://purl.org/dc/elements/1.1/> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

<{public_url}> a sd:Service ;
    rdfs:label "{title}" ;
    dc:description "{description}" ;
    sd:endpoint <{public_url}> ;
    sd:supportedLanguage sd:SPARQL11Query ;
    sd:resultFormat <http://www.w3.org/ns/formats/SPARQL_Results_JSON>, <http://www.w3.org/ns/formats/SPARQL_Results_CSV> ;
    sd:feature sd:DereferencesURIs ;
    sd:defaultEntailmentRegime ent:RDFS ;
    sd:defaultDataset [
        a sd:Dataset ;
        sd:defaultGraph [
            a sd:Graph ;
        ]
    ] .
""".rstrip()


class SparqlEndpoint(FastAPI):
    """
    Class to deploy a SPARQL endpoint using a RDFLib Graph.
    """

    def __init__(
        self,
        *args: Any,
        title: str = "SPARQL endpoint for RDFLib graph",
        description: str = "A SPARQL endpoint to serve machine learning models, or any other logic implemented in Python. \n[Source code](https://github.com/vemonet/rdflib-endpoint)",
        version: str = "0.1.0",
        graph: Union[None, Graph, ConjunctiveGraph, Dataset] = None,
        functions: Optional[Dict[str, Callable[..., Any]]] = None,
        custom_eval: Optional[Callable[..., Any]] = None,
        enable_update: bool = False,
        cors_enabled: bool = True,
        public_url: str = "https://sparql.openpredict.semanticscience.org/sparql",
        example_query: str = EXAMPLE_SPARQL,
        **kwargs: Any,
    ) -> None:
        """
        Constructor of the SPARQL endpoint, everything happens here.
        FastAPI calls are defined in this constructor
        """
        self.graph = graph if graph is not None else ConjunctiveGraph()
        self.functions = functions if functions is not None else {}
        self.title = title
        self.description = description
        self.version = version
        self.public_url = public_url
        self.example_query = example_query
        self.example_markdown = f"Example query:\n\n```\n{example_query}\n```"
        self.enable_update = enable_update

        # Instantiate FastAPI
        super().__init__(
            *args,
            title=title,
            description=description,
            version=version,
            **kwargs,
        )

        # Save custom function in custom evaluation dictionary
        # Handle multiple functions directly in the evalCustomFunctions function
        if custom_eval:
            rdflib.plugins.sparql.CUSTOM_EVALS["evalCustomFunctions"] = custom_eval
        else:
            rdflib.plugins.sparql.CUSTOM_EVALS["evalCustomFunctions"] = self.eval_custom_functions

        if cors_enabled:
            self.add_middleware(
                CORSMiddleware,
                allow_origins=["*"],
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )

        # api_responses: Dict[int, Dict] = {
        api_responses: Optional[Dict[Union[int, str], Dict[str, Any]]] = {
            200: {
                "description": "SPARQL query results",
                "content": {
                    "application/sparql-results+json": {
                        "results": {"bindings": []},
                        "head": {"vars": []},
                    },
                    "application/json": {
                        "results": {"bindings": []},
                        "head": {"vars": []},
                    },
                    "text/csv": {"example": "s,p,o"},
                    "application/sparql-results+csv": {"example": "s,p,o"},
                    "text/turtle": {"example": "service description"},
                    "application/sparql-results+xml": {"example": "<root></root>"},
                    "application/xml": {"example": "<root></root>"},
                    # "application/rdf+xml": {
                    #     "example": '<?xml version="1.0" encoding="UTF-8"?> <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"></rdf:RDF>'
                    # },
                },
            },
            400: {
                "description": "Bad Request",
            },
            403: {
                "description": "Forbidden",
            },
            422: {
                "description": "Unprocessable Entity",
            },
        }

        mimetype = {
            "turtle": "text/turtle",
            "xml_results": "application/sparql-results+xml",
        }

        @self.middleware("http")
        async def add_process_time_header(request: Request, call_next: Any) -> Response:
            start_time = time.time()
            response: Response = await call_next(request)
            process_time = time.time() - start_time
            response.headers["X-Process-Time"] = str(process_time)
            return response

        @self.get(
            "/sparql",
            name="SPARQL endpoint",
            description=self.example_markdown,
            responses=api_responses,
        )
        async def sparql_endpoint(request: Request, query: Optional[str] = Query(None)) -> Response:
            """
            Send a SPARQL query to be executed through HTTP GET operation.

            :param request: The HTTP GET request
            :param query: SPARQL query input.
            """
            if not query:
                # Return the SPARQL endpoint service description
                service_graph = Graph()
                # service_graph.parse('app/service-description.ttl', format="ttl")
                service_graph.parse(data=service_description_ttl, format="ttl")

                # Add custom functions URI to the service description
                for custom_function_uri in self.functions:
                    service_graph.add(
                        (
                            URIRef(custom_function_uri),
                            RDF.type,
                            URIRef("http://www.w3.org/ns/sparql-service-description#Function"),
                        )
                    )
                    service_graph.add(
                        (
                            URIRef(self.public_url),
                            URIRef("http://www.w3.org/ns/sparql-service-description#extensionFunction"),
                            URIRef(custom_function_uri),
                        )
                    )

                # Return the service description RDF as turtle or XML
                if request.headers["accept"] == mimetype["turtle"]:
                    return Response(
                        service_graph.serialize(format="turtle"),
                        media_type=mimetype["turtle"],
                    )
                else:
                    return Response(
                        service_graph.serialize(format="xml"),
                        media_type="application/xml",
                    )

            # Pretty print the query object
            # from rdflib.plugins.sparql.algebra import pprintAlgebra
            # parsed_query = parser.parseQuery(query)
            # tq = algebraTranslateQuery(parsed_query)
            # pprintAlgebra(tq)

            graph_ns = dict(self.graph.namespaces())

            try:
                # Query the graph with the custom functions loaded
                parsed_query = prepareQuery(query, initNs=graph_ns)
                query_operation = re.sub(r"(\w)([A-Z])", r"\1 \2", parsed_query.algebra.name)
            except Exception as e:
                logging.error("Error parsing the SPARQL query: " + str(e))
                return JSONResponse(
                    status_code=400,
                    content={"message": "Error parsing the SPARQL query"},
                )

            # Useless: RDFLib doesn't support SPARQL insert (Expected {SelectQuery | ConstructQuery | DescribeQuery | AskQuery}, found 'INSERT')
            # if not self.enable_update:
            #     if query_operation == "Insert Query" or query_operation == "Delete Query":
            #         return JSONResponse(status_code=403, content={"message": "INSERT and DELETE queries are not allowed."})
            # if os.getenv('RDFLIB_APIKEY') and (query_operation == "Insert Query" or query_operation == "Delete Query"):
            #     if apikey != os.getenv('RDFLIB_APIKEY'):
            #         return JSONResponse(status_code=403, content={"message": "Wrong API KEY."})

            try:
                # query_results = self.graph.query(query, initNs=graph_ns)
                query_results = self.graph.query(query)
            except Exception as e:
                logging.error("Error executing the SPARQL query on the RDFLib Graph: " + str(e))
                return JSONResponse(
                    status_code=400,
                    content={"message": "Error executing the SPARQL query on the RDFLib Graph"},
                )

            # Format and return results depending on Accept mime type in request header
            output_mime_type = request.headers["accept"]
            if not output_mime_type:
                output_mime_type = "application/xml"

            # Handle mime type for construct queries
            if query_operation == "Construct Query" and (
                output_mime_type == "application/json" or output_mime_type == "text/csv"
            ):
                output_mime_type = mimetype["turtle"]
                # TODO: support JSON-LD for construct query?
                # g.serialize(format='json-ld', indent=4)
            if query_operation == "Construct Query" and output_mime_type == "application/xml":
                output_mime_type = "application/rdf+xml"

            try:
                if output_mime_type == "text/csv" or output_mime_type == "application/sparql-results+csv":
                    return Response(
                        query_results.serialize(format="csv"),
                        media_type=output_mime_type,
                    )
                elif output_mime_type == "application/json" or output_mime_type == "application/sparql-results+json":
                    return Response(
                        query_results.serialize(format="json"),
                        media_type=output_mime_type,
                    )
                elif output_mime_type == "application/xml" or output_mime_type == mimetype["xml_results"]:
                    return Response(
                        query_results.serialize(format="xml"),
                        media_type=output_mime_type,
                    )
                elif output_mime_type == mimetype["turtle"]:
                    # .serialize(format='turtle').decode("utf-8")
                    return Response(
                        query_results.serialize(format="turtle"),
                        media_type=output_mime_type,
                    )
                else:
                    # XML by default for federated queries
                    return Response(
                        query_results.serialize(format="xml"),
                        media_type=mimetype["xml_results"],
                    )
            except Exception as e:
                logging.error("Error serializing the SPARQL query results with RDFLib: " + str(e))
                return JSONResponse(
                    status_code=422,
                    content={"message": "Error serializing the SPARQL query results"},
                )

        @self.post(
            "/sparql",
            name="SPARQL endpoint",
            description=self.example_markdown,
            responses=api_responses,
        )
        async def post_sparql_endpoint(request: Request, query: Optional[str] = Query(None)) -> Response:
            """Send a SPARQL query to be executed through HTTP POST operation.

            :param request: The HTTP POST request with a .body()
            :param query: SPARQL query input.
            """
            if not query:
                # Handle federated query services which provide the query in the body
                query_body = await request.body()
                body = query_body.decode("utf-8")
                parsed_query = parse.parse_qsl(body)
                for params in parsed_query:
                    if params[0] == "query":
                        query = parse.unquote(params[1])
            return await sparql_endpoint(request, query)

        @self.get("/", include_in_schema=False)
        async def serve_yasgui() -> Response:
            """Serve YASGUI interface"""
            with open(pkg_resources.resource_filename("rdflib_endpoint", "yasgui.html")) as f:
                html_str = f.read()
            html_str = html_str.replace("$EXAMPLE_QUERY", self.example_query)
            return Response(content=html_str, media_type="text/html")

        # Service description returned when no query provided
        service_description_ttl = SERVICE_DESCRIPTION_TTL_FMT.format(
            public_url=self.public_url,
            title=self.title,
            description=self.description.replace("\n", ""),
        )

    def eval_custom_functions(self, ctx: QueryContext, part: CompValue) -> List[Any]:
        """Retrieve variables from a SPARQL-query, then execute registered SPARQL functions
        The results are then stored in Literal objects and added to the query results.

        :param ctx:     <class 'rdflib.plugins.sparql.sparql.QueryContext'>
        :param part:    <class 'rdflib.plugins.sparql.parserutils.CompValue'>
        :return:        <class 'rdflib.plugins.sparql.processor.SPARQLResult'>
        """
        # This part holds basic implementation for adding new functions
        if part.name == "Extend":
            query_results: List[Any] = []

            # Information is retrieved and stored and passed through a generator
            for eval_part in evalPart(ctx, part.p):
                # Checks if the function is a URI (custom function)
                if hasattr(part.expr, "iri"):
                    # Iterate through the custom functions passed in the constructor
                    for function_uri, custom_function in self.functions.items():
                        # Check if URI correspond to a registered custom function
                        if part.expr.iri == URIRef(function_uri):
                            # Execute each function
                            query_results, ctx, part, _ = custom_function(query_results, ctx, part, eval_part)

                else:
                    # For built-in SPARQL functions (that are not URIs)
                    evaluation: List[Any] = [_eval(part.expr, eval_part.forget(ctx, _except=part._vars))]
                    if isinstance(evaluation[0], SPARQLError):
                        raise evaluation[0]
                    # Append results for built-in SPARQL functions
                    for result in evaluation:
                        query_results.append(eval_part.merge({part.var: Literal(result)}))

            return query_results
        raise NotImplementedError()
