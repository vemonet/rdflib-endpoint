import sys
import glob
import click
from rdflib import ConjunctiveGraph
from rdflib_endpoint import SparqlEndpoint
import uvicorn


@click.group()
def cli():
    """Quickly serve RDF files as SPARQL endpoint with RDFLib Endpoint"""
    pass


@cli.command(help='Serve a local RDF file as a SPARQL endpoint by default on http://0.0.0.0:8000/sparql')
@click.argument('files', nargs=-1)
@click.option('--host', default='0.0.0.0', help='Host of the SPARQL endpoint')
@click.option('--port', default=8000, help='Port of the SPARQL endpoint')
def serve(files, host, port):
    run_serve(files, host, port)


def run_serve(files, host, port):
    g = ConjunctiveGraph()
    for glob_file in files:
        file_list = glob.glob(glob_file)
        for file in file_list:
            g.parse(file)
            click.echo(click.style('INFO', fg='green') 
                + f':     📥️ Loaded triples from ' + click.style(str(file), bold=True)
                + f', for a total of ' + click.style(str(len(g)), bold=True))
    
    app = SparqlEndpoint(graph=g)
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    sys.exit(cli())