import time
from multiprocessing import Process

import httpx
import pytest
import uvicorn
from example.main import ds

# from testcontainers.core.container import DockerContainer
# from testcontainers.core.waiting_utils import wait_for_logs
from rdflib_endpoint import SparqlEndpoint

# https://github.com/biopragmatics/curies/blob/main/tests/test_federated_sparql.py


def _get_app():
    return SparqlEndpoint(
        graph=ds,
        enable_update=True,
    )


@pytest.fixture(scope="module")
def service_url():
    host = "localhost"
    port = 8000
    service_process = Process(
        target=uvicorn.run,
        args=(_get_app,),
        kwargs={"host": host, "port": port, "log_level": "info"},
        daemon=True,
    )
    service_process.start()
    time.sleep(2)
    endpoint_url = f"http://{host}:{port}"
    yield endpoint_url
    service_process.kill()
    service_process.join()


def test_direct_custom_concat(service_url):
    custom_function_query = """PREFIX func: <https://w3id.org/sparql-functions/>
SELECT ?input ?part ?partIndex WHERE {
    VALUES ?input { "hello world" "cheese is good" }
    BIND(func:splitIndex(?input, " ") AS ?part)
}"""
    response = httpx.get(service_url, params={"query": custom_function_query}, headers={"accept": "application/json"})
    # print(response.text)
    assert response.status_code == 200
    assert response.json()["results"]["bindings"][0]["part"]["value"] == "hello"


# Stop and delete all testcontainers: docker stop $(docker ps -a -q) && docker rm $(docker ps -a -q)
# NOTE: in case issue in rootless docker: https://github.com/testcontainers/testcontainers-python/issues/537
# TESTCONTAINERS_DOCKER_SOCKET_OVERRIDE=/run/user/$(id -u)/docker.sock uv run pytest tests/test_federation.py -s

# import os

# env = os.environ.copy()
# env["GRAPHDB_USERNAME"] = "admin"
# env["GRAPHDB_PASSWORD"] = "root"

# @pytest.fixture(scope="module")
# def graphdb():
#     """Start GraphDB container as a fixture."""
#     container = DockerContainer("ontotext/graphdb:10.8.4")
#     container.with_exposed_ports(7200).with_bind_ports(7200, 7200)
#     container.with_env("JAVA_OPTS", "-Xms1g -Xmx4g")
#     container.start()
#     delay = wait_for_logs(container, "Started GraphDB")
#     base_url = f"http://{container.get_container_host_ip()}:{container.get_exposed_port(7200)}"

#     print(f"GraphDB started in {delay:.0f}s at {base_url}")
#     # print(container.get_logs())
#     yield base_url


# def test_graphdb_custom_concat(service_url, graphdb):
#     print(concat_select.format(rdflib_endpoint_url=service_url))
#     response = httpx.get(graphdb, params={"query": concat_select.format(rdflib_endpoint_url=service_url)}, headers={"accept": "application/json"})
#     print(response.text)
#     assert response.status_code == 200
#     assert response.json()["results"]["bindings"][0]["concat"]["value"] == "Firstlast"


# @pytest.fixture(scope="module")
# def blazegraph():
#     """Start blazegraph container as a fixture."""
#     container = DockerContainer("lyrasis/blazegraph:2.1.4")
#     container.with_exposed_ports(8080).with_bind_ports(8080, 8080)
#     # container.with_env("JAVA_OPTS", "-Xms1g -Xmx4g")
#     container.start()
#     delay = wait_for_logs(container, "Started @")
#     base_url = f"http://{container.get_container_host_ip()}:{container.get_exposed_port(8080)}/bigdata/namespace/kb/sparql"

#     print(f"Blazegraph started in {delay:.0f}s at {base_url}")
#     # print(container.get_logs())
#     yield base_url


# def test_blazegraph_custom_concat(service_url, blazegraph):
#     print(concat_select.format(rdflib_endpoint_url=service_url))
#     response = httpx.get(blazegraph, params={"query": concat_select.format(rdflib_endpoint_url=service_url)}, headers={"accept": "application/json"})
#     print(response.text)
#     assert response.status_code == 200
#     assert response.json()["results"]["bindings"][0]["concat"]["value"] == "Firstlast"


# custom_fed_query = """PREFIX func: <https://w3id.org/sparql-functions/>
# SELECT ?input ?part ?partIndex WHERE {{
#     SERVICE <{rdflib_endpoint_url}> {{
#         VALUES ?input { "hello world" "cheese is good" }
#         BIND(func:splitIndex(?input, " ") AS ?part)
#     }}
# }}"""
