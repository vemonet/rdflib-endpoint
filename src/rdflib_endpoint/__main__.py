import glob
import sys
from typing import List

import click
import uvicorn
from rdflib import ConjunctiveGraph

from rdflib_endpoint import SparqlEndpoint


@click.group()
def cli() -> None:
    """Quickly serve RDF files as SPARQL endpoint with RDFLib Endpoint"""


@cli.command(help="Serve a local RDF file as a SPARQL endpoint by default on http://0.0.0.0:8000/sparql")
@click.argument("files", nargs=-1)
@click.option("--host", default="localhost", help="Host of the SPARQL endpoint")
@click.option("--port", default=8000, help="Port of the SPARQL endpoint")
@click.option("--store", default="default", help="Store used by RDFLib: default or Oxigraph")
def serve(files: list[str], host: str, port: int, store: str) -> None:
    run_serve(files, host, port, store)


def run_serve(files: List[str], host: str, port: int, store: str = "default") -> None:
    if store == "oxigraph":
        store = store.capitalize()
    g = ConjunctiveGraph(store=store)
    for glob_file in files:
        file_list = glob.glob(glob_file)
        for file in file_list:
            g.parse(file)
            click.echo(
                click.style("INFO", fg="green")
                + ":     📥️ Loaded triples from "
                + click.style(str(file), bold=True)
                + ", for a total of "
                + click.style(str(len(g)), bold=True)
            )

    app = SparqlEndpoint(
        graph=g,
        example_query="""PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT * WHERE {
    GRAPH ?g {
        ?s ?p ?o .
    }
} LIMIT 100""",
    )
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    sys.exit(cli())
