import sys
import click
from rdflib import ConjunctiveGraph
from rdflib_endpoint import SparqlEndpoint
import uvicorn


@click.group()
def cli():
    """Quickly serve RDF files as SPARQL endpoint with RDFLib Endpoint"""
    pass


@cli.command(help='Serve a local RDF file as a SPARQL endpoint by default on http://0.0.0.0:8000/sparql')
@click.argument('file', nargs=1)
@click.option('--host', default='0.0.0.0', help='Host of the SPARQL endpoint')
@click.option('--port', default=8000, help='Port of the SPARQL endpoint')
def serve(file, host, port):
    run_serve(file, host, port)


def run_serve(file, host, port):
    g = ConjunctiveGraph()
    g.parse(file)
    app = SparqlEndpoint(
        graph=g
    )
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    print('exxiiiit')
    sys.exit(cli())