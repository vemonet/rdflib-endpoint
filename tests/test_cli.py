import glob
import os
import tempfile
import time
from multiprocessing import Process

import pkg_resources
import pytest
import requests
from click.testing import CliRunner

from rdflib_endpoint.__main__ import cli


def run_cli():
    runner = CliRunner()
    return runner.invoke(
        cli,
        [
            "serve",
            pkg_resources.resource_filename("tests", "resources/test.nq"),
            pkg_resources.resource_filename("tests", "resources/test2.ttl"),
            pkg_resources.resource_filename("tests", "resources/another.jsonld"),
        ],
    )


@pytest.fixture
def server(scope="module"):
    proc = Process(target=run_cli, args=(), daemon=True)
    proc.start()
    time.sleep(1)
    yield proc
    proc.kill()


def test_query_cli(server):
    resp = requests.get(
        "http://localhost:8000/?query=" + select_all_query,
        headers={"accept": "application/json"},
        timeout=600,
    )
    assert len(resp.json()["results"]["bindings"]) > 2


select_all_query = """SELECT * WHERE {
    ?s ?p ?o .
}"""


def test_convert():
    with tempfile.NamedTemporaryFile(delete=True) as tmp_file:
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["convert", pkg_resources.resource_filename("tests", "resources/test2.ttl"), "--output", str(tmp_file)],
        )
        assert result.exit_code == 0
        with open(str(tmp_file)) as file:
            content = file.read()
            assert "ns0:s" in content

    # Fix issue with python creating unnecessary temp files on disk
    for f in glob.glob("<tempfile._TemporaryFileWrapper*"):
        os.remove(f)
