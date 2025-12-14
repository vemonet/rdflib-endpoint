import pytest
from example.main import custom_concat
from fastapi.testclient import TestClient
from rdflib import RDFS, Graph, Literal, URIRef

from rdflib_endpoint import SparqlEndpoint
from rdflib_endpoint.sparql_router import SD

# graph = Dataset(default_union=False)
graph = Graph()


@pytest.fixture(autouse=True)
def clear_graph():
    # Workaround to clear graph without putting
    # graph, app and endpoint into a fixture
    # and modifying the test fixture usage.
    for triple in graph:
        graph.remove(triple)


app = SparqlEndpoint(
    graph=graph,
    functions={
        "https://w3id.org/sparql-functions/custom_concat": custom_concat,
    },
    enable_update=True,
)

endpoint = TestClient(app)


def test_service_description():
    # Check GET turtle
    response = endpoint.get("/", headers={"accept": "text/turtle"})
    assert response.status_code == 200
    g = Graph()
    g.parse(data=response.text, format="turtle")
    assert any(g.triples((None, SD.endpoint, None))), "Missing sd:endpoint in service description"
    assert any(g.triples((None, SD.extensionFunction, None))), "Missing sd:extensionFunction in service description"
    assert len(list(g.triples((None, SD.extensionFunction, None)))) == 1, "Expected exactly 1 extension function"

    # Check POST XML
    response = endpoint.post("/", headers={"accept": "application/xml"})
    assert response.status_code == 200
    g = Graph()
    g.parse(data=response.text, format="xml")
    assert any(g.triples((None, SD.endpoint, None))), "Missing sd:endpoint in service description"
    assert any(g.triples((None, SD.extensionFunction, None))), "Missing sd:extensionFunction in service description"
    assert len(list(g.triples((None, SD.extensionFunction, None)))) == 1, "Expected exactly 1 extension function"


def test_custom_concat_json():
    response = endpoint.get("/", params={"query": concat_select}, headers={"accept": "application/json"})
    # print(response.json())
    assert response.status_code == 200
    assert response.json()["results"]["bindings"][0]["concat"]["value"] == "Firstlast"

    response = endpoint.post("/", data={"query": concat_select}, headers={"accept": "application/json"})
    assert response.status_code == 200
    assert response.json()["results"]["bindings"][0]["concat"]["value"] == "Firstlast"

    response = endpoint.post(
        "/", data=concat_select, headers={"accept": "application/json", "content-type": "application/sparql-query"}
    )
    assert response.status_code == 200
    assert response.json()["results"]["bindings"][0]["concat"]["value"] == "Firstlast"


def test_select_noaccept_xml():
    response = endpoint.post("/", data={"query": concat_select})
    assert response.status_code == 200
    assert response.text.startswith("<?xml ")


def test_select_csv():
    response = endpoint.post("/", data={"query": concat_select}, headers={"accept": "text/csv"})
    assert response.status_code == 200


label_patch = """
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
DELETE { ?subject rdfs:label "foo" }
INSERT { ?subject rdfs:label "bar" }
WHERE { ?subject rdfs:label "foo" }
"""


@pytest.mark.parametrize(
    "api_key,key_provided,param_method",
    [
        (api_key, key_provided, param_method)
        for api_key in [None, "key"]
        for key_provided in [True, False]
        for param_method in ["body_form", "body_direct"]
    ],
)
def test_sparql_update(api_key, key_provided, param_method, monkeypatch):
    if api_key:
        monkeypatch.setenv("RDFLIB_APIKEY", api_key)
    subject = URIRef("http://server.test/subject")
    headers = {}
    if key_provided:
        headers["Authorization"] = "Bearer key"
    graph.add((subject, RDFS.label, Literal("foo")))
    if param_method == "body_form":
        request_args = {"data": {"update": label_patch}}
    else:
        # direct
        headers["content-type"] = "application/sparql-update"
        request_args = {"data": label_patch}
    response = endpoint.post("/", headers=headers, **request_args)
    if api_key is None or key_provided:
        assert response.status_code == 204
        assert (subject, RDFS.label, Literal("foo")) not in graph
        assert (subject, RDFS.label, Literal("bar")) in graph
    else:
        assert response.status_code == 403
        assert (subject, RDFS.label, Literal("foo")) in graph
        assert (subject, RDFS.label, Literal("bar")) not in graph


def test_sparql_query_update_fail():
    response = endpoint.post("/", data={"update": label_patch, "query": label_patch})
    assert response.status_code == 400


def test_multiple_accept_return_json():
    response = endpoint.get(
        "/",
        params={"query": concat_select},
        headers={"accept": "text/html;q=0.3, application/xml;q=0.9, application/json, */*;q=0.8"},
    )
    assert response.status_code == 200
    assert response.json()["results"]["bindings"][0]["concat"]["value"] == "Firstlast"


def test_multiple_accept_return_json2():
    response = endpoint.get(
        "/",
        params={"query": concat_select},
        headers={"accept": "text/html;q=0.3, application/json, application/xml;q=0.9, */*;q=0.8"},
    )
    assert response.status_code == 200
    assert response.json()["results"]["bindings"][0]["concat"]["value"] == "Firstlast"


def test_select_turtle():
    response = endpoint.post("/", data={"query": concat_select}, headers={"accept": "text/turtle"})
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/sparql-results+xml"


def test_concat_construct_turtle():
    response = endpoint.post(
        "/",
        data={"query": custom_concat_construct},
        headers={"accept": "text/turtle"},
    )
    assert response.status_code == 200
    assert response.text.startswith("@prefix ")


def test_concat_construct_csv():
    response = endpoint.post(
        "/",
        data={"query": custom_concat_construct},
        headers={"accept": "text/csv"},
    )
    assert response.status_code == 200
    assert response.text.startswith("@prefix ")


def test_concat_construct_jsonld():
    response = endpoint.post(
        "/",
        data={"query": custom_concat_construct},
        headers={"accept": "application/json"},
    )
    assert response.status_code == 200
    assert response.json()[0]["@id"] == "http://example.com/test"


def test_concat_construct_xml():
    # expected to return turtle
    response = endpoint.post(
        "/",
        data={"query": custom_concat_construct},
        headers={"accept": "application/xml"},
    )
    assert response.status_code == 200
    assert response.text.startswith("<?xml ")


def test_concat_construct_rdf_xml_with_two_accept_options():
    response = endpoint.post(
        "/",
        data={"query": custom_concat_construct},
        headers={"accept": "application/sparql-results+xml, application/rdf+xml"},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/rdf+xml"
    assert response.text.startswith("<?xml ")
    assert "<rdf:RDF" in response.text


def test_yasgui():
    # expected to return turtle
    response = endpoint.get(
        "/",
        headers={"accept": "text/html"},
    )
    assert response.status_code == 200


def test_bad_request():
    response = endpoint.get("/?query=figarofigarofigaro", headers={"accept": "application/json"})
    assert response.status_code == 400


concat_select = """PREFIX myfunctions: <https://w3id.org/sparql-functions/>
SELECT ?concat ?concatLength WHERE {
    BIND("First" AS ?first)
    BIND(myfunctions:custom_concat(?first, "last") AS ?concat)
}"""

custom_concat_construct = """PREFIX myfunctions: <https://w3id.org/sparql-functions/>
CONSTRUCT {
    <http://example.com/test> <http://example.com/concat> ?concat, ?concatLength .
} WHERE {
    BIND("First" AS ?first)
    BIND(myfunctions:custom_concat(?first, "last") AS ?concat)
}"""
