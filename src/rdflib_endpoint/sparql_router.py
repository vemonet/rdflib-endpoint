import logging
import os
import re
from importlib import resources
from typing import Any, Callable, Dict, List, Optional, Union
from urllib import parse

import rdflib
from fastapi import APIRouter, Query, Request, Response
from fastapi.responses import JSONResponse
from rdflib import RDF, ConjunctiveGraph, Dataset, Graph, Literal, URIRef
from rdflib.plugins.sparql import prepareQuery, prepareUpdate
from rdflib.plugins.sparql.evaluate import evalPart
from rdflib.plugins.sparql.evalutils import _eval
from rdflib.plugins.sparql.parserutils import CompValue
from rdflib.plugins.sparql.sparql import QueryContext, SPARQLError
from rdflib.query import Processor

__all__ = [
    "SparqlRouter",
]

DEFAULT_TITLE: str = "SPARQL endpoint for RDFLib graph"
DEFAULT_DESCRIPTION: str = "A SPARQL endpoint to serve machine learning models, or any other logic implemented in Python. \n[Source code](https://github.com/vemonet/rdflib-endpoint)"
DEFAULT_VERSION: str = "0.1.0"
DEFAULT_PUBLIC_URL: str = "https://your-endpoint/sparql"
DEFAULT_FAVICON: str = "https://rdflib.readthedocs.io/en/stable/_static/RDFlib.png"
DEFAULT_EXAMPLE = """\
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

api_responses: Optional[Dict[Union[int, str], Dict[str, Any]]] = {
    200: {
        "description": "SPARQL query results",
        "content": {
            "application/sparql-results+json": {"example": {"results": {"bindings": []}, "head": {"vars": []}}},
            "application/json": {"example": {"results": {"bindings": []}, "head": {"vars": []}}},
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

#: This is default for federated queries
DEFAULT_CONTENT_TYPE = "application/xml"

#: A mapping from content types to the keys used for serializing
#: in :meth:`rdflib.Graph.serialize` and other serialization functions
CONTENT_TYPE_TO_RDFLIB_FORMAT = {
    # https://www.w3.org/TR/sparql11-results-json/
    "application/sparql-results+json": "json",
    "application/json": "json",
    "text/json": "json",
    # https://www.w3.org/TR/rdf-sparql-XMLres/
    "application/sparql-results+xml": "xml",
    "application/xml": "xml",  # for compatibility
    "application/rdf+xml": "xml",  # for compatibility
    "text/xml": "xml",  # not standard
    # https://www.w3.org/TR/sparql11-results-csv-tsv/
    "application/sparql-results+csv": "csv",
    "text/csv": "csv",  # for compatibility
    # Extras
    "text/turtle": "ttl",
}


def parse_accept_header(accept: str) -> List[str]:
    """
    Given an accept header string, return a list of media types in order of preference.

    :param accept: Accept header value
    :return: Ordered list of media type preferences
    """

    def _parse_preference(qpref: str) -> float:
        qparts = qpref.split("=")
        try:
            return float(qparts[1].strip())
        except (ValueError, IndexError):
            pass
        return 1.0

    preferences = []
    types = accept.split(",")
    dpref = 2.0
    for mtype in types:
        parts = mtype.split(";")
        parts = [part.strip() for part in parts]
        pref = dpref
        try:
            for part in parts[1:]:
                if part.startswith("q="):
                    pref = _parse_preference(part)
                    break
        except IndexError:
            pass
        # preserve order of appearance in the list
        dpref = dpref - 0.01
        preferences.append((parts[0], pref))
    preferences.sort(key=lambda x: -x[1])
    return [pref[0] for pref in preferences]


class SparqlRouter(APIRouter):
    """
    Class to deploy a SPARQL endpoint using a RDFLib Graph.
    """

    def __init__(
        self,
        *args: Any,
        path: str = "/",
        title: str = DEFAULT_TITLE,
        description: str = DEFAULT_DESCRIPTION,
        version: str = DEFAULT_VERSION,
        graph: Union[None, Graph, ConjunctiveGraph, Dataset] = None,
        processor: Union[str, Processor] = "sparql",
        custom_eval: Optional[Callable[..., Any]] = None,
        functions: Optional[Dict[str, Callable[..., Any]]] = None,
        enable_update: bool = False,
        public_url: str = DEFAULT_PUBLIC_URL,
        favicon: str = DEFAULT_FAVICON,
        example_query: str = DEFAULT_EXAMPLE,
        example_queries: Optional[Dict[str, Dict[str, str]]] = None,
        **kwargs: Any,
    ) -> None:
        """
        Constructor of the SPARQL endpoint, everything happens here.
        FastAPI calls are defined in this constructor
        """
        self.graph = graph if graph is not None else ConjunctiveGraph()
        self.functions = functions if functions is not None else {}
        self.processor = processor
        self.title = title
        self.description = description
        self.version = version
        self.path = path
        self.public_url = public_url
        self.example_query = example_query
        self.example_queries = example_queries
        self.example_markdown = f"Example query:\n\n```\n{example_query}\n```"
        self.enable_update = enable_update
        self.favicon = favicon

        # Instantiate APIRouter
        super().__init__(
            *args,
            responses=api_responses,
            **kwargs,
        )

        # Save custom function in custom evaluation dictionary
        # Handle multiple functions directly in the evalCustomFunctions function
        if custom_eval:
            rdflib.plugins.sparql.CUSTOM_EVALS["evalCustomFunctions"] = custom_eval
        elif len(self.functions) > 0:
            rdflib.plugins.sparql.CUSTOM_EVALS["evalCustomFunctions"] = self.eval_custom_functions

        async def handle_sparql_request(
            request: Request, query: Optional[str] = None, update: Optional[str] = None
        ) -> Response:
            """Handle SPARQL requests to the GET and POST endpoints"""
            if query and update:
                return JSONResponse(
                    status_code=400,
                    content={"message": "Cannot do both query and update"},
                )

            if not query and not update:
                if str(request.headers["accept"]).startswith("text/html"):
                    return self.serve_yasgui()
                # If not asking HTML, return the SPARQL endpoint service description
                service_graph = self.get_service_graph()

                # Return the service description RDF as turtle or XML
                if request.headers["accept"] == "text/turtle":
                    return Response(
                        service_graph.serialize(format="turtle"),
                        media_type="text/turtle",
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

            if query:
                try:
                    parsed_query = prepareQuery(query, initNs=graph_ns)
                    query_results = self.graph.query(parsed_query, processor=self.processor)

                    # Format and return results depending on Accept mime type in request header
                    mime_types = parse_accept_header(request.headers.get("accept", DEFAULT_CONTENT_TYPE))

                    # Handle cases that are more complicated, like it includes multiple
                    # types, extra information, etc.
                    output_mime_type = DEFAULT_CONTENT_TYPE
                    for mime_type in mime_types:
                        if mime_type in CONTENT_TYPE_TO_RDFLIB_FORMAT:
                            output_mime_type = mime_type
                            # Use the first mime_type that matches
                            break

                    query_operation = re.sub(r"(\w)([A-Z])", r"\1 \2", parsed_query.algebra.name)

                    # Handle mime type for construct queries
                    if query_operation == "Construct Query":
                        if output_mime_type in {"application/json", "text/csv"}:
                            output_mime_type = "text/turtle"
                            # TODO: support JSON-LD for construct query?
                            # g.serialize(format='json-ld', indent=4)
                        elif output_mime_type == "application/xml":
                            output_mime_type = "application/rdf+xml"
                        else:
                            pass  # TODO what happens here?

                    try:
                        rdflib_format = CONTENT_TYPE_TO_RDFLIB_FORMAT[output_mime_type]
                        response = Response(
                            query_results.serialize(format=rdflib_format),
                            media_type=output_mime_type,
                        )
                    except Exception as e:
                        logging.error(f"Error serializing the SPARQL query results with RDFLib: {e}")
                        return JSONResponse(
                            status_code=422,
                            content={"message": f"Error serializing the SPARQL query results with RDFLib: {e}"},
                        )
                    else:
                        return response
                except Exception as e:
                    logging.error(f"Error executing the SPARQL query on the RDFLib Graph: {e}")
                    return JSONResponse(
                        status_code=400,
                        content={"message": f"Error executing the SPARQL query on the RDFLib Graph: {e}"},
                    )
            else:  # Update
                if not self.enable_update:
                    return JSONResponse(
                        status_code=403, content={"message": "INSERT and DELETE queries are not allowed."}
                    )
                if rdflib_apikey := os.environ.get("RDFLIB_APIKEY"):
                    authorized = False
                    if auth_header := request.headers.get("Authorization"):  # noqa: SIM102
                        if auth_header.startswith("Bearer ") and auth_header[7:] == rdflib_apikey:
                            authorized = True
                    if not authorized:
                        return JSONResponse(status_code=403, content={"message": "Invalid API KEY."})
                try:
                    prechecked_update: str = update  # type: ignore
                    parsed_update = prepareUpdate(prechecked_update, initNs=graph_ns)
                    self.graph.update(parsed_update, "sparql")
                    return Response(status_code=204)
                except Exception as e:
                    logging.error(f"Error executing the SPARQL update on the RDFLib Graph: {e}")
                    return JSONResponse(
                        status_code=400,
                        content={"message": f"Error executing the SPARQL update on the RDFLib Graph: {e}"},
                    )

        # TODO: use add_api_route? https://github.com/tiangolo/fastapi/blob/d666ccb62216e45ca78643b52c235ba0d2c53986/fastapi/routing.py#L548
        @self.get(
            self.path,
            name="SPARQL endpoint",
            description=self.example_markdown,
            responses=api_responses,
        )
        async def get_sparql_endpoint(
            request: Request,
            query: Optional[str] = Query(None),
        ) -> Response:
            """
            Send a SPARQL query to be executed through HTTP GET operation.

            :param request: The HTTP GET request
            :param query: SPARQL query input.
            """
            return await handle_sparql_request(request, query=query)

        @self.post(
            path,
            name="SPARQL endpoint",
            description=self.example_markdown,
            responses=api_responses,
        )
        async def post_sparql_endpoint(request: Request) -> Response:
            """Send a SPARQL query to be executed through HTTP POST operation.

            :param request: The HTTP POST request with a .body()
            """
            request_body = await request.body()
            body = request_body.decode("utf-8")
            content_type = request.headers.get("content-type")
            if content_type == "application/sparql-query":
                query = body
                update = None
            elif content_type == "application/sparql-update":
                query = None
                update = body
            elif content_type == "application/x-www-form-urlencoded":
                request_params = parse.parse_qsl(body)
                query_params = [kvp[1] for kvp in request_params if kvp[0] == "query"]
                query = parse.unquote(query_params[0]) if query_params else None
                update_params = [kvp[1] for kvp in request_params if kvp[0] == "update"]
                update = parse.unquote(update_params[0]) if update_params else None
                # TODO: handle params `using-graph-uri` and `using-named-graph-uri`
                # https://www.w3.org/TR/sparql11-protocol/#update-operation
            else:
                # Response with the service description
                query = None
                update = None
            return await handle_sparql_request(request, query, update)

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

    def serve_yasgui(self) -> Response:
        """Serve YASGUI interface"""
        import json

        with resources.open_text("rdflib_endpoint", "yasgui.html") as f:
            html_str = f.read()
        html_str = html_str.replace("$TITLE", self.title)
        html_str = html_str.replace("$DESCRIPTION", self.description)
        html_str = html_str.replace("$FAVICON", self.favicon)
        html_str = html_str.replace("$EXAMPLE_QUERY", self.example_query)
        html_str = html_str.replace("$EXAMPLE_QUERIES", json.dumps(self.example_queries))
        return Response(content=html_str, media_type="text/html")

    def get_service_graph(self) -> rdflib.Graph:
        # Service description returned when no query provided
        service_description_ttl = SERVICE_DESCRIPTION_TTL_FMT.format(
            public_url=self.public_url,
            title=self.title,
            description=self.description.replace("\n", ""),
        )
        graph = Graph()
        graph.parse(data=service_description_ttl, format="ttl")
        # service_graph.parse('app/service-description.ttl', format="ttl")

        # Add custom functions URI to the service description
        for custom_function_uri in self.functions:
            graph.add(
                (
                    URIRef(custom_function_uri),
                    RDF.type,
                    URIRef("http://www.w3.org/ns/sparql-service-description#Function"),
                )
            )
            graph.add(
                (
                    URIRef(self.public_url),
                    URIRef("http://www.w3.org/ns/sparql-service-description#extensionFunction"),
                    URIRef(custom_function_uri),
                )
            )

        return graph
