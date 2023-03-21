import time
from typing import Any, Callable, Dict, Optional, Union

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from rdflib import ConjunctiveGraph, Dataset, Graph
from rdflib.query import Processor

from rdflib_endpoint import SparqlRouter

__all__ = [
    "SparqlEndpoint",
]


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
        processor: Union[str, Processor] = "sparql",
        custom_eval: Optional[Callable[..., Any]] = None,
        enable_update: bool = False,
        cors_enabled: bool = True,
        path: str = "/",
        public_url: str = "https://sparql.openpredict.semanticscience.org/sparql",
        example_query: Optional[str] = None,
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

        # if self.path != "/":
        #     logging.info(f"SPARQL endpoint running on \033[1mhttp://localhost:8000{self.path}\033[0m")

        @self.middleware("http")
        async def add_process_time_header(request: Request, call_next: Any) -> Response:
            start_time = time.time()
            response: Response = await call_next(request)
            process_time = time.time() - start_time
            response.headers["X-Process-Time"] = str(process_time)
            return response
