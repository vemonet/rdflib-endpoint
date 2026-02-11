import time
from typing import Any, Callable, Dict, Optional, Union

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from rdflib import Dataset, Graph
from rdflib.query import Processor

from rdflib_endpoint.sparql_router import SparqlRouter
from rdflib_endpoint.utils import Defaults, QueryExample


class SparqlEndpoint(FastAPI):
    """Class to deploy a SPARQL endpoint using a RDFLib Graph."""

    def __init__(
        self,
        *args: Any,
        path: str = "/",
        title: str = Defaults.title,
        description: str = Defaults.description,
        version: str = Defaults.version,
        graph: Union[None, Graph, Dataset] = None,
        functions: Optional[Dict[str, Callable[..., Any]]] = None,
        processor: Union[str, Processor] = "sparql",
        custom_eval: Optional[Callable[..., Any]] = None,
        enable_update: bool = False,
        cors_enabled: bool = True,
        public_url: str = Defaults.public_url,
        favicon: str = Defaults.favicon,
        example_queries: Optional[Dict[str, QueryExample]] = None,
        example_query: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """
        Create a SPARQL endpoint.

        It's mainly a wrapper to include the SPARQL router. Everything happens in the router.

        Args:
            path: The path where the SPARQL endpoint will be available.
            title: A title for the SPARQL endpoint.
            description: A description for the SPARQL endpoint.
            version: A version for the SPARQL endpoint.
            graph: An RDFLib `Graph` or `Dataset` to be served as a SPARQL endpoint. If None, an empty `Dataset` with default union is used.
            functions: LEGACY: a dictionary of custom functions
            processor: The RDFLib query processor to use.
            custom_eval: A custom function to evaluate SPARQL queries.
            enable_update: Whether to enable SPARQL Update queries.
            cors_enabled: Whether to enable CORS for the endpoint.
            public_url: The public URL of the endpoint, used for the SPARQL service description and for the YASGUI example queries.
            favicon: A URL to a favicon to be used for the endpoint.
            example_queries: A dictionary of example queries to be displayed in YASGUI tabs. If empty and a `DatasetExt` with custom functions is provided, they will be extracted from docstrings.
            example_query: DEPRECATED: use `example_queries` instead, the first one will be used as default YASGUI tab.
        """
        self.title = title
        self.description = description
        self.version = version

        # Instantiate FastAPI
        super().__init__(
            *args,
            title=title,
            description=description,
            version=version,
            **kwargs,
        )

        sparql_router = SparqlRouter(
            path=path,
            title=title,
            description=description,
            version=version,
            graph=graph,
            functions=functions,
            processor=processor,
            custom_eval=custom_eval,
            enable_update=enable_update,
            public_url=public_url,
            favicon=favicon,
            example_queries=example_queries,
            example_query=example_query,
        )
        self.include_router(sparql_router)

        if cors_enabled:
            self.add_middleware(
                CORSMiddleware,
                allow_origins=["*"],
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )

        @self.middleware("http")
        async def add_process_time_header(request: Request, call_next: Any) -> Response:
            """Add a Server-Timing header with the total processing time for each request."""
            start_time = time.time()
            response: Response = await call_next(request)
            response.headers["Server-Timing"] = f"total;dur={time.time() - start_time}"
            return response
