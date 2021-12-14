# from fastapi.testclient import TestClient
import pytest
# from click.testing import CliRunner
# from rdflib_endpoint.__main__ import cli 
# import pkg_resources
# import requests
# from multiprocessing import Process

## Unfortunately pytest is not mature enough to perform a basic task like yielding a generic HTTP service
## they can only do it for really specific services for which you need to builb testing classes
## Using multiprocessing does not work in the first place, so I am not keen on spending time fixing all the dumb issues pytest will have
## simply deploying a simple HTTP service on a local host and port should be the most basic stuff they should be handling 


# def run_server():
#     runner = CliRunner()
#     runner.invoke(cli, ['serve', pkg_resources.resource_filename('tests', 'resources/test.nt')])


# @pytest.fixture
# def server(scope="module"):
#     proc = Process(target=run_server, args=(), daemon=True)
#     proc.start() 
#     yield proc
#     proc.kill()


# def test_serve(server):
#     resp = requests.get('http://0.0.0.0:8000/sparql?query=' + select_all_query)
#     assert len(resp.json()['results']['bindings']) > 0


# select_all_query = """SELECT * WHERE {
#     ?s ?p ?o .
# }"""