import pytest
from click.testing import CliRunner
from rdflib_endpoint.__main__ import cli 
import pkg_resources
import requests
from multiprocessing import Process
import time


def run_cli():
    runner = CliRunner()
    return runner.invoke(cli, ['serve', pkg_resources.resource_filename('tests', 'resources/test.nt')])


@pytest.fixture
def server(scope="module"):
    proc = Process(target=run_cli, args=(), daemon=True)
    proc.start()
    time.sleep(1)
    yield proc
    proc.kill()


def test_query_cli(server):
    resp = requests.get('http://0.0.0.0:8000/sparql?query=' + select_all_query, 
        headers={'accept': 'application/json'})
    assert len(resp.json()['results']['bindings']) > 0


select_all_query = """SELECT * WHERE {
    ?s ?p ?o .
}"""