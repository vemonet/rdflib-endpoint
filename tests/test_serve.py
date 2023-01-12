import time
from multiprocessing import Process

import pkg_resources
import pytest
import requests

from rdflib_endpoint.__main__ import run_serve


@pytest.fixture
def server(scope="module"):
    print(pkg_resources.resource_filename("tests", "resources/test.nq"))
    proc = Process(
        target=run_serve,
        args=(
            [pkg_resources.resource_filename("tests", "resources/test.nq")],
            "localhost",
            8000,
        ),
        daemon=True,
    )
    proc.start()
    time.sleep(1)
    yield proc
    proc.kill()


def test_query_serve(server):
    resp = requests.get(
        "http://localhost:8000/sparql?query=" + select_all_query,
        headers={"accept": "application/json"},
        timeout=600,
    )
    assert len(resp.json()["results"]["bindings"]) > 0


select_all_query = """SELECT * WHERE {
    ?s ?p ?o .
}"""
