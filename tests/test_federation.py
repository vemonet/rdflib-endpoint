import os
import platform
import time
from multiprocessing import Process, set_start_method

import httpx
import pytest
import uvicorn
from example.main import ds
from testcontainers.core.container import DockerContainer
from testcontainers.core.waiting_utils import wait_for_logs

from rdflib_endpoint import SparqlEndpoint

# https://github.com/biopragmatics/curies/blob/main/tests/test_federated_sparql.py
# Stop and delete all testcontainers:
# docker stop $(docker ps -a -q) && docker rm $(docker ps -a -q)
# $DOCKER_HOST needs to be set, e.g. for orbstack:
# export DOCKER_HOST=unix:///Users/$(whoami)/.orbstack/run/docker.sock uv run pytest tests/test_federation.py -s


def _get_app():
    return SparqlEndpoint(
        graph=ds,
        enable_update=True,
    )


custom_fed_query = """PREFIX func: <urn:sparql-function:>
SELECT ?input ?part ?partIndex WHERE {{
    SERVICE <{rdflib_endpoint_url}> {{
        VALUES ?input {{ "hello world" "cheese is good" }}
        BIND(func:splitIndex(?input, " ") AS ?part)
    }}
}}"""


@pytest.fixture(scope="module")
def service_url():
    # Force multiprocessing fork start method for compatibility with unpicklable objects, to fix this on py3.8 and 3.9
    set_start_method("fork", force=True)
    host = "0.0.0.0"  # noqa: S104
    port = 8000
    service_process = Process(
        target=uvicorn.run,
        args=(_get_app,),
        kwargs={"host": host, "port": port, "log_level": "info"},
        daemon=True,
    )
    service_process.start()
    time.sleep(2)
    # Use host.docker.internal on macOS (Docker Desktop), 172.17.0.1 on Linux (GitHub Actions)
    host_ip = "host.docker.internal" if platform.system() == "Darwin" else "172.17.0.1"
    endpoint_url = f"http://{host_ip}:{port}"
    yield endpoint_url
    service_process.kill()
    service_process.join()


def test_direct_query(service_url):
    custom_function_query = """PREFIX func: <urn:sparql-function:>
SELECT ?input ?part ?partIndex WHERE {
    VALUES ?input { "hello world" "cheese is good" }
    BIND(func:splitIndex(?input, " ") AS ?part)
}"""
    response = httpx.get(
        "http://localhost:8000",
        params={"query": custom_function_query},
        headers={"accept": "application/json"},
    )
    # print(response.text)
    assert response.status_code == 200
    assert response.json()["results"]["bindings"][0]["part"]["value"] == "hello"


admin_password = "root"  # noqa: S105
graphdb_username = "admin"

env = os.environ.copy()
env["GRAPHDB_USERNAME"] = graphdb_username
env["GRAPHDB_PASSWORD"] = admin_password


@pytest.fixture(scope="module")
def graphdb():
    """Start GraphDB container as a fixture."""
    container = DockerContainer("ontotext/graphdb:10.8.4")
    container.with_exposed_ports(7200).with_bind_ports(7200, 7200)
    # container.with_env("JAVA_OPTS", "-Xms1g -Xmx4g")
    container.start()
    delay = wait_for_logs(container, "Started GraphDB")
    base_url = f"http://{container.get_container_host_ip()}:{container.get_exposed_port(7200)}"
    print(f"GraphDB started in {delay:.0f}s at {base_url}")
    # print(container.get_logs())
    # Create repository https://graphdb.ontotext.com/documentation/10.8/manage-repos-with-restapi.html
    config = """@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix rep: <http://www.openrdf.org/config/repository#> .
@prefix sr: <http://www.openrdf.org/config/repository/sail#> .
@prefix sail: <http://www.openrdf.org/config/sail#> .
[] a rep:Repository ;
    rep:repositoryID "testfed" ;
    rdfs:label "Test Federation Repository" ;
    rep:repositoryImpl [
        rep:repositoryType "graphdb:SailRepository" ;
        sr:sailImpl [ sail:sailType "graphdb:Sail" ]
    ] ."""
    response = httpx.post(
        f"{base_url}/rest/repositories",
        files={"config": ("repo-config.ttl", config, "text/turtle")},
        auth=(graphdb_username, admin_password),
    )
    assert response.status_code == 201, f"Failed to create repository: {response.text}"
    yield f"{base_url}/repositories/testfed"


def test_federated_query_graphdb(service_url, graphdb):
    # print(custom_fed_query.format(rdflib_endpoint_url="http://host.docker.internal:8000"))
    response = httpx.post(
        graphdb,
        data={"query": custom_fed_query.format(rdflib_endpoint_url=service_url)},
        headers={"accept": "application/sparql-results+json"},
    )
    print(response.text)
    assert response.status_code == 200
    assert response.json()["results"]["bindings"][0]["part"]["value"] == "hello"


@pytest.fixture(scope="module")
def blazegraph():
    """Start blazegraph container as a fixture."""
    container = DockerContainer("lyrasis/blazegraph:2.1.4")
    container.with_exposed_ports(8080).with_bind_ports(8080, 8080)
    container.start()
    delay = wait_for_logs(container, "Started @")
    base_url = (
        f"http://{container.get_container_host_ip()}:{container.get_exposed_port(8080)}/bigdata/namespace/kb/sparql"
    )
    print(f"Blazegraph started in {delay:.0f}s at {base_url}")
    # print(container.get_logs())
    yield base_url


def test_federated_query_blazegraph(service_url, blazegraph):
    # print(custom_fed_query.format(rdflib_endpoint_url=service_url))
    response = httpx.post(
        blazegraph,
        data={"query": custom_fed_query.format(rdflib_endpoint_url=service_url)},
        headers={"accept": "application/sparql-results+json"},
    )
    print(response.text)
    assert response.status_code == 200
    assert response.json()["results"]["bindings"][0]["part"]["value"] == "hello"


@pytest.fixture(scope="module")
def oxigraph():
    """Start oxigraph container as a fixture."""
    container = DockerContainer("oxigraph/oxigraph:latest")
    container.with_exposed_ports(7878).with_bind_ports(7878, 7878)
    container.start()
    delay = wait_for_logs(container, "Listening for requests at")
    base_url = f"http://{container.get_container_host_ip()}:{container.get_exposed_port(7878)}/query"
    print(f"Oxigraph started in {delay:.0f}s at {base_url}")
    # print(container.get_logs())
    yield base_url


def test_federated_query_oxigraph(service_url, oxigraph):
    response = httpx.post(
        oxigraph,
        data={"query": custom_fed_query.format(rdflib_endpoint_url=service_url)},
        headers={"accept": "application/sparql-results+json"},
    )
    print(response.text)
    assert response.status_code == 200
    assert response.json()["results"]["bindings"][0]["part"]["value"] == "hello"


@pytest.fixture(scope="module")
def fuseki():
    """Start fuseki container as a fixture."""
    container = DockerContainer("stain/jena-fuseki:latest")
    container.with_exposed_ports(3030).with_bind_ports(3030, 3030)
    container.with_env("ADMIN_PASSWORD", admin_password)
    container.start()
    delay = wait_for_logs(container, "Fuseki is available")
    base_url = f"http://{container.get_container_host_ip()}:{container.get_exposed_port(3030)}"
    print(f"Fuseki started in {delay:.0f}s at {base_url}")
    # Create dataset
    response = httpx.post(
        f"{base_url}/$/datasets",
        data={"dbName": "testfed", "dbType": "tdb2"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        auth=("admin", admin_password),
    )
    assert response.status_code == 200, f"Failed to create dataset: {response.text}"
    # print(container.get_logs())
    yield f"{base_url}/testfed/sparql"


def test_federated_query_fuseki(service_url, fuseki):
    response = httpx.post(
        fuseki,
        data={"query": custom_fed_query.format(rdflib_endpoint_url=service_url)},
        headers={"accept": "application/sparql-results+json"},
    )
    print(response.text)
    assert response.status_code == 200
    assert response.json()["results"]["bindings"][0]["part"]["value"] == "hello"


@pytest.fixture(scope="module")
def rdf4j():
    """Start rdf4j container as a fixture."""
    container = DockerContainer("eclipse/rdf4j-workbench:latest")
    container.with_exposed_ports(8080).with_bind_ports(8080, 8081)
    # container.with_env("JAVA_OPTS", "-Xms1g -Xmx4g")
    container.start()
    delay = wait_for_logs(container, "Server startup in")
    base_url = f"http://{container.get_container_host_ip()}:{container.get_exposed_port(8080)}/rdf4j-server/repositories/testfed"
    print(f"rdf4j started in {delay:.0f}s at {base_url}")
    # print(container.get_logs())
    # Create repository https://graphdb.ontotext.com/documentation/10.8/manage-repos-with-restapi.html
    config = """@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>.
@prefix config: <tag:rdf4j.org,2023:config/>.
@prefix sail: <http://www.openrdf.org/config/sail#> .
@prefix sr: <http://www.openrdf.org/config/repository/sail#> .
[] a config:Repository ;
    config:rep.id "testfed" ;
    rdfs:label "Test Repository" ;
    config:rep.impl [
        config:rep.type "openrdf:SailRepository" ;
        sr:sailImpl [ sail:sailType "openrdf:MemoryStore" ; ]
    ] ."""
    response = httpx.put(base_url, content=config, headers={"Content-Type": "text/turtle"})
    assert response.status_code == 204, f"Failed to create repository: {response.text}"
    yield base_url


def test_federated_query_rdf4j(service_url, rdf4j):
    response = httpx.post(
        rdf4j,
        data={"query": custom_fed_query.format(rdflib_endpoint_url=service_url)},
        headers={"accept": "application/sparql-results+json"},
    )
    print(response.text)
    assert response.status_code == 200
    assert response.json()["results"]["bindings"][0]["part"]["value"] == "hello"


# Virtuoso https://community.openlinksw.com/t/enabling-sparql-1-1-federated-query-processing-in-virtuoso/2477
# docker run -it -e DBA_PASSWORD=dba -p 8890:8890 --rm openlink/virtuoso-opensource-7:latest
# """
# isql -U dba -P dba exec='GRANT "SPARQL_SELECT_FED" TO "SPARQL";'
# isql -U dba -P dba exec='GRANT "SPARQL_LOAD_SERVICE_DATA" TO "SPARQL";'
# isql -U dba -P dba exec='GRANT SELECT ON DB.DBA.SPARQL_SINV_2 TO "SPARQL";'
# isql -U dba -P dba exec='GRANT EXECUTE ON DB.DBA.SPARQL_SINV_IMP TO "SPARQL";'
# """

# @pytest.fixture(scope="module")
# def virtuoso():
#     """Start virtuoso container as a fixture."""
#     container = DockerContainer("openlink/virtuoso-opensource-7:latest")
#     container.with_exposed_ports(8890).with_bind_ports(8890, 8890)
#     container.with_env("VIRT_SPARQL_AllowQueryService", "1")
#     container.with_env("DBA_PASSWORD", admin_password)
#     container.start()
#     delay = wait_for_logs(container, "Server online at")
#     base_url = f"http://{container.get_container_host_ip()}:{container.get_exposed_port(8890)}/sparql"

#     # Enable federated queries
#     container.exec(f'isql -U dba -P {admin_password} exec=\'GRANT "SPARQL_SELECT_FED" TO "SPARQL";\'')
#     container.exec(f'isql -U dba -P {admin_password} exec=\'GRANT "SPARQL_LOAD_SERVICE_DATA" TO "SPARQL";\'')
#     container.exec(f'isql -U dba -P {admin_password} exec=\'GRANT SELECT ON DB.DBA.SPARQL_SINV_2 TO "SPARQL";\'')
#     container.exec(f'isql -U dba -P {admin_password} exec=\'GRANT EXECUTE ON DB.DBA.SPARQL_SINV_IMP TO "SPARQL";\'')
#     container.exec("apt-get update")
#     container.exec("apt-get install -y curl")
#     print(container.exec("curl -I http://host.docker.internal:8000"))
#     # container.exec(f'isql -U dba -P {admin_password} exec=\'GRANT SPARQL_UPDATE ON GRAPH <http://host.docker.internal:8000> TO "SPARQL";\'')
#     time.sleep(5)
#     print(f"Virtuoso started in {delay:.0f}s at {base_url}")
#     yield base_url


# def test_federated_query_virtuoso(service_url, virtuoso):
#     # NOTE: getting error when sending an extension function to virtuoso
#     # Virtuoso RDF02 Error SR619: SPARUL LOAD SERVICE DATA access denied: database user 107 (SPARQL) has no write permission on graph http://host.docker.internal:8000
#     # response = httpx.post(virtuoso, data={"query": custom_fed_query.format(rdflib_endpoint_url=service_url)}, headers={"accept": "application/sparql-results+json"})

#     # ERROR: Virtuoso HTCLI Error HC001: Connection Error in HTTP Client
#     virtuoso_fed_query = """PREFIX dc: <http://purl.org/dc/elements/1.1/>
# SELECT ?id WHERE {{
#     SERVICE <{rdflib_endpoint_url}> {{
#         <https://identifiers.org/CHEBI/1> dc:identifier ?id .
#     }}
# }}"""
#     response = httpx.post(virtuoso, data={"query": virtuoso_fed_query.format(rdflib_endpoint_url=service_url)}, headers={"accept": "application/sparql-results+json"})
#     print(response.text)
#     assert response.status_code == 200
#     assert response.json()["results"]["bindings"][0]["id"]["value"] == "https://identifiers.org/chebi/1"


# Qlever
# docker run -it --rm -p 7001:7001 adfreiburg/qlever -c "mkdir -p /tmp/empty-db && cd /tmp/empty-db && touch empty.nt && qlever setup-config empty && qlever settings --format nt --input-files empty.nt && qlever index && qlever start"
# docker run -it --rm -p 7001:7001 adfreiburg/qlever -c "qlever setup-config olympics && qlever get-data && qlever index && qlever start"

# @pytest.fixture(scope="module")
# def qlever():
#     """Start qlever container as a fixture."""
#     container = DockerContainer("adfreiburg/qlever:commit-f35a290")
#     container.with_exposed_ports(7001).with_bind_ports(7001, 7001)
#     container.start()
#     delay = wait_for_logs(container, "Started @")
#     base_url = f"http://{container.get_container_host_ip()}:{container.get_exposed_port(7001)}/sparql"
#     print(f"QLever started in {delay:.0f}s at {base_url}")
#     # print(container.get_logs())
#     yield base_url

# def test_federated_query_qlever(service_url, qlever):
#     # print(custom_fed_query.format(rdflib_endpoint_url=service_url))
#     response = httpx.post(qlever, data={"query": custom_fed_query.format(rdflib_endpoint_url=service_url)}, headers={"accept": "application/sparql-results+json"})
#     print(response.text)
#     assert response.status_code == 200
#     assert response.json()["results"]["bindings"][0]["part"]["value"] == "hello"
