import time
from typing import Any, Callable, Dict, Optional, Union

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from rdflib import Dataset, Graph
from rdflib.query import Processor

from rdflib_endpoint.sparql_router import (
    DEFAULT_DESCRIPTION,
    DEFAULT_EXAMPLE,
    DEFAULT_FAVICON,
    DEFAULT_PUBLIC_URL,
    DEFAULT_TITLE,
    DEFAULT_VERSION,
    QueryExample,
    SparqlRouter,
)

__all__ = [
    "SparqlEndpoint",
]


class SparqlEndpoint(FastAPI):
    """Class to deploy a SPARQL endpoint using a RDFLib Graph."""

    def __init__(
        self,
        *args: Any,
        path: str = "/",
        title: str = DEFAULT_TITLE,
        description: str = DEFAULT_DESCRIPTION,
        version: str = DEFAULT_VERSION,
        graph: Union[None, Graph, Dataset] = None,
        functions: Optional[Dict[str, Callable[..., Any]]] = None,
        processor: Union[str, Processor] = "sparql",
        custom_eval: Optional[Callable[..., Any]] = None,
        enable_update: bool = False,
        cors_enabled: bool = True,
        public_url: str = DEFAULT_PUBLIC_URL,
        example_query: str = DEFAULT_EXAMPLE,
        example_queries: Optional[Dict[str, QueryExample]] = None,
        favicon: str = DEFAULT_FAVICON,
        **kwargs: Any,
    ) -> None:
        """
        Constructor of the SPARQL endpoint, it's mainly a wrapper to include the SPARQL router. Everything happens in the router.
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
            example_query=example_query,
            example_queries=example_queries,
            favicon=favicon,
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
