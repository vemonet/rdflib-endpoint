import logging
import os
import re
from importlib import resources
from typing import Any, Callable, Dict, List, Optional, Union
from urllib import parse

import rdflib
from fastapi import APIRouter, Query, Request, Response
from fastapi.responses import JSONResponse
from rdflib import RDF, BNode, Dataset, Graph, Literal, URIRef
from rdflib.namespace import DC, RDFS
from rdflib.plugins.sparql import prepareQuery, prepareUpdate
from rdflib.plugins.sparql.evaluate import evalPart
from rdflib.plugins.sparql.evalutils import _eval
from rdflib.plugins.sparql.parserutils import CompValue
from rdflib.plugins.sparql.sparql import QueryContext, SPARQLError
from rdflib.query import Processor

from rdflib_endpoint.utils import (
    API_RESPONSES,
    CONTENT_TYPE_TO_RDFLIB_FORMAT,
    FORMATS,
    SD,
    Defaults,
    QueryExample,
    parse_accept_header,
)

__all__ = [
    "SparqlRouter",
]


class SparqlRouter(APIRouter):
    """Class to deploy a SPARQL endpoint using a RDFLib Graph."""

    def __init__(
        self,
        *args: Any,
        path: str = "/",
        title: str = Defaults.title,
        description: str = Defaults.description,
        version: str = Defaults.version,
        graph: Union[None, Graph, Dataset] = None,
        service_description: Union[None, Graph] = None,
        processor: Union[str, Processor] = "sparql",
        custom_eval: Optional[Callable[..., Any]] = None,
        functions: Optional[Dict[str, Callable[..., Any]]] = None,
        enable_update: bool = False,
        public_url: str = Defaults.public_url,
        favicon: str = Defaults.favicon,
        example_query: str = Defaults.example,
        example_queries: Optional[Dict[str, QueryExample]] = None,
        **kwargs: Any,
    ) -> None:
        """Create a SPARQL endpoint router.

        The endpoints calls are all defined in this constructor
        """
        self.graph = graph if graph is not None else Dataset(default_union=True)
        """RDFLib Graph for the SPARQL endpoint."""
        self.service_description = service_description if service_description is not None else Graph()
        """RDFLib Graph for the SPARQL Service description."""
        self.functions = functions if functions is not None else {}
        """Custom SPARQL functions to use in the SPARQL queries."""
        self.processor = processor
        """Custom RDFLib SPARQL processor to use for the SPARQL queries."""
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
            responses=API_RESPONSES,
            **kwargs,
        )

        # Save custom function in custom evaluation dictionary
        # Handle multiple functions directly in the evalCustomFunctions function
        if custom_eval:
            rdflib.plugins.sparql.CUSTOM_EVALS["evalCustomFunctions"] = custom_eval
        elif len(self.functions) > 0:
            rdflib.plugins.sparql.CUSTOM_EVALS["evalCustomFunctions"] = self.eval_custom_functions

        self.prepare_sd_graph()

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
                if str(request.headers.get("accept", "")).startswith("text/html"):
                    return self.serve_yasgui()
                # If not asking HTML, return the SPARQL endpoint service description
                if request.headers.get("accept") == "text/turtle":
                    return Response(
                        self.service_description.serialize(format="turtle"),
                        media_type="text/turtle",
                    )
                else:
                    return Response(
                        self.service_description.serialize(format="xml"),
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
                    mime_types = parse_accept_header(request.headers.get("accept", Defaults.content_type))

                    # Handle cases that are more complicated, like it includes multiple
                    # types, extra information, etc.
                    output_mime_type = Defaults.content_type
                    for mime_type in mime_types:
                        if mime_type in CONTENT_TYPE_TO_RDFLIB_FORMAT:
                            output_mime_type = mime_type
                            # Use the first mime_type that matches
                            break

                    query_operation = re.sub(r"(\w)([A-Z])", r"\1 \2", parsed_query.algebra.name)

                    # Handle mime type for construct queries
                    if query_operation == "Construct Query":
                        if output_mime_type == "text/csv":
                            output_mime_type = "text/turtle"
                        elif output_mime_type == "application/json":
                            output_mime_type = "application/ld+json"
                        elif output_mime_type == "application/xml":
                            output_mime_type = "application/rdf+xml"
                        else:
                            pass

                    try:
                        rdflib_format = CONTENT_TYPE_TO_RDFLIB_FORMAT.get(output_mime_type, output_mime_type)
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
            responses=API_RESPONSES,
        )
        async def get_sparql_endpoint(
            request: Request,
            query: Optional[str] = Query(None),
        ) -> Response:
            """Send a SPARQL query to be executed through HTTP GET operation.

            :param request: The HTTP GET request
            :param query: SPARQL query input.
            """
            return await handle_sparql_request(request, query=query)

        @self.post(
            path,
            name="SPARQL endpoint",
            description=self.example_markdown,
            responses=API_RESPONSES,
        )
        async def post_sparql_endpoint(request: Request) -> Response:
            """Send a SPARQL query to be executed through HTTP POST operation.

            :param request: The HTTP POST request with a .body()
            """
            request_body = await request.body()
            body = request_body.decode("utf-8")
            content_type = request.headers.get("content-type", "")
            if "application/sparql-query" in content_type:
                query = body
                update = None
            elif "application/sparql-update" in content_type:
                query = None
                update = body
            elif "application/x-www-form-urlencoded" in content_type:
                request_params = parse.parse_qsl(body)
                query_params = [kvp[1] for kvp in request_params if kvp[0] == "query"]
                query = parse.unquote(query_params[0]) if query_params else None
                update_params = [kvp[1] for kvp in request_params if kvp[0] == "update"]
                update = parse.unquote(update_params[0]) if update_params else None
                # TODO: handle params `using-graph-uri` and `using-named-graph-uri`
                # https://www.w3.org/TR/sparql11-protocol/#update-operation
            elif not body and request.query_params:
                # Blazegraph SERVICE calls uses query_params, not body
                query = parse.unquote(request.query_params.get("query", ""))
                update = request.query_params.get("update")
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

    def prepare_sd_graph(self) -> None:
        """Prepare the endpoint Service Description graph"""
        # https://www.w3.org/TR/sparql12-service-description/
        self.service_description.bind("rdfs", "http://www.w3.org/2000/01/rdf-schema#")
        self.service_description.bind("dc", "http://purl.org/dc/elements/1.1/")
        self.service_description.bind("sd", SD)
        self.service_description.bind("ent", "http://www.w3.org/ns/entailment/")
        self.service_description.bind("prof", "http://www.w3.org/ns/owl-profile/")
        self.service_description.bind("void", "http://rdfs.org/ns/void#")
        self.service_description.bind("formats", FORMATS)
        sd_subj = next(self.service_description.subjects(SD.endpoint, None), None) or BNode()

        if (sd_subj, RDF.type, SD.Service) not in self.service_description:
            self.service_description.add((sd_subj, RDF.type, SD.Service))

        # Check and add endpoint, label and description
        if not any(self.service_description.triples((sd_subj, SD.endpoint, None))):
            self.service_description.add((sd_subj, SD.endpoint, URIRef(self.public_url)))
        if not any(self.service_description.triples((sd_subj, RDFS.label, None))):
            self.service_description.add((sd_subj, RDFS.label, Literal(self.title)))
        if not any(self.service_description.triples((sd_subj, DC.description, None))):
            self.service_description.add((sd_subj, DC.description, Literal(self.description)))

        # Check and add supported language
        if not any(self.service_description.triples((sd_subj, SD.supportedLanguage, SD.SPARQL11Query))):
            self.service_description.add((sd_subj, SD.supportedLanguage, SD.SPARQL11Query))
            if self.enable_update:
                self.service_description.add((sd_subj, SD.supportedLanguage, SD.SPARQL11Update))

        # Add features
        if (
            isinstance(self.graph, Dataset)
            and getattr(self.graph, "default_union", False)
            and not any(self.service_description.triples((sd_subj, SD.feature, SD.BasicFederatedQuery)))
        ):
            self.service_description.add((sd_subj, SD.feature, SD.UnionDefaultGraph))
        if not any(self.service_description.triples((sd_subj, SD.feature, SD.BasicFederatedQuery))):
            self.service_description.add((sd_subj, SD.feature, SD.BasicFederatedQuery))

        # Add result formats
        if not any(self.service_description.triples((sd_subj, SD.resultFormat, FORMATS.SPARQL_Results_JSON))):
            self.service_description.add((sd_subj, SD.resultFormat, FORMATS.SPARQL_Results_JSON))
        if not any(self.service_description.triples((sd_subj, SD.resultFormat, FORMATS.SPARQL_Results_CSV))):
            self.service_description.add((sd_subj, SD.resultFormat, FORMATS.SPARQL_Results_CSV))
        if not any(self.service_description.triples((sd_subj, SD.resultFormat, FORMATS.Turtle))):
            self.service_description.add((sd_subj, SD.resultFormat, FORMATS.Turtle))
        if not any(self.service_description.triples((sd_subj, SD.resultFormat, FORMATS.RDF_XML))):
            self.service_description.add((sd_subj, SD.resultFormat, FORMATS.RDF_XML))

        # Add input formats
        if not any(self.service_description.triples((sd_subj, SD.inputFormat, None))):
            self.service_description.add((sd_subj, SD.inputFormat, FORMATS.RDF_XML))
            self.service_description.add((sd_subj, SD.inputFormat, FORMATS.Turtle))
            self.service_description.add((sd_subj, SD.inputFormat, FORMATS.JSON_LD))
            self.service_description.add((sd_subj, SD.inputFormat, FORMATS.N_Triples))
            self.service_description.add((sd_subj, SD.inputFormat, FORMATS.N_Quads))
            self.service_description.add((sd_subj, SD.inputFormat, FORMATS.TriG))

        # Check and add entailment regime
        # sd_default_entailment_regime = URIRef("http://www.w3.org/ns/sparql-service-description#defaultEntailmentRegime")
        # ent_rdfs = URIRef("http://www.w3.org/ns/entailment/RDFS")
        # if not any(self.service_description.triples((service_uri, sd_default_entailment_regime, ent_rdfs))):
        #     self.service_description.add((service_uri, sd_default_entailment_regime, ent_rdfs))

        # Check if default dataset exists, if not add it
        has_dataset = False
        dataset_node = None
        for _s, _p, o in self.service_description.triples((sd_subj, SD.defaultDataset, None)):
            has_dataset = True
            dataset_node = o
            break

        if not has_dataset:
            dataset_node = rdflib.BNode()
            self.service_description.add((sd_subj, SD.defaultDataset, dataset_node))
            self.service_description.add((dataset_node, RDF.type, SD.Dataset))

            # Add default graph to the dataset
            graph_node = rdflib.BNode()
            self.service_description.add((dataset_node, SD.defaultGraph, graph_node))
            self.service_description.add((graph_node, RDF.type, SD.Graph))

            # Add named graphs to the dataset
            if isinstance(self.graph, Dataset):
                # Get the list of distinct graph names with a SPARQL query
                results: Any = self.graph.query("SELECT DISTINCT ?g WHERE { GRAPH ?g { ?s ?p ?o } }")

                for row in results:
                    named_graph_node = rdflib.BNode()
                    graph_node = rdflib.BNode()

                    # Add the named graph reference
                    self.service_description.add((dataset_node, SD.namedGraph, named_graph_node))
                    self.service_description.add((named_graph_node, RDF.type, SD.NamedGraph))
                    self.service_description.add((named_graph_node, SD.name, row.g))
                    # self.service_description.add((named_graph_node, SD.entailmentRegime, URIRef("http://www.w3.org/ns/entailment/OWL-RDF-Based")))
                    # self.service_description.add((named_graph_node, SD.supportedEntailmentProfile, URIRef("http://www.w3.org/ns/owl-profile/RL")))

                    # Add graph metadata
                    self.service_description.add((named_graph_node, SD.graph, graph_node))
                    self.service_description.add((graph_node, RDF.type, SD.Graph))

                    # Count triples in the named graph and add it to the description
                    triple_count_query = f"SELECT (COUNT(*) AS ?count) WHERE {{ GRAPH <{row.g}> {{ ?s ?p ?o }} }}"
                    count_result: Any = self.graph.query(triple_count_query)
                    triple_count = next(iter(count_result), [Literal(0)])[0]
                    # result_row: Any = next(iter(count_result), None)
                    # triple_count = result_row.count if result_row else Literal(0)
                    self.service_description.add((graph_node, URIRef("http://rdfs.org/ns/void#triples"), triple_count))

        # Add custom functions to the service description
        for custom_function_uri in self.functions:
            function_uri = URIRef(custom_function_uri)

            if (function_uri, RDF.type, SD.Function) not in self.service_description:
                self.service_description.add((function_uri, RDF.type, SD.Function))
            if (sd_subj, SD.extensionFunction, function_uri) not in self.service_description:
                self.service_description.add((sd_subj, SD.extensionFunction, function_uri))
        # return self.service_description

        # Add custom functions URI to the service description
        for custom_function_uri in self.functions:
            self.service_description.add(
                (
                    URIRef(custom_function_uri),
                    RDF.type,
                    SD.Function,
                )
            )
            self.service_description.add(
                (
                    sd_subj,
                    SD.extensionFunction,
                    URIRef(custom_function_uri),
                )
            )
