from fastapi.testclient import TestClient
from rdflib import RDF, RDFS, Graph, Literal, URIRef

from rdflib_endpoint import SparqlEndpoint

g = Graph(store="Oxigraph")
g.add((URIRef("http://subject"), RDF.type, URIRef("http://object")))
g.add((URIRef("http://subject"), RDFS.label, Literal("test value")))


app = SparqlEndpoint(graph=g)

endpoint = TestClient(app)


def test_service_description():
    response = endpoint.get("/", headers={"accept": "text/turtle"})
    # print(response.text.strip())
    assert response.status_code == 200

    response = endpoint.post("/", headers={"accept": "text/turtle"})
    assert response.status_code == 200

    # Check for application/xml
    response = endpoint.post("/", headers={"accept": "application/xml"})
    assert response.status_code == 200


def test_custom_concat_json():
    response = endpoint.get("/?query=", params={"query": label_select}, headers={"accept": "application/json"})
    assert response.status_code == 200
    assert response.json()["results"]["bindings"][0]["label"]["value"] == "test value"

    response = endpoint.post("/", data={"query": label_select}, headers={"accept": "application/json"})
    assert response.status_code == 200
    assert response.json()["results"]["bindings"][0]["label"]["value"] == "test value"


def test_select_noaccept_xml():
    response = endpoint.post("/", data={"query": label_select})
    assert response.status_code == 200
    # assert response.json()['results']['bindings'][0]['concat']['value'] == "Firstlast"


def test_select_csv():
    response = endpoint.post("/", data={"query": label_select}, headers={"accept": "text/csv"})
    assert response.status_code == 200
    # assert response.json()['results']['bindings'][0]['concat']['value'] == "Firstlast"


def test_select_turtle():
    response = endpoint.post("/", data={"query": label_select}, headers={"accept": "text/turtle"})
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/sparql-results+xml"
    # assert response.json()['results']['bindings'][0]['concat']['value'] == "Firstlast"


def test_concat_construct_turtle():
    # expected to return turtle
    response = endpoint.post(
        "/",
        data="query=" + label_construct,
        headers={"accept": "application/json"},
    )
    assert response.status_code == 200
    # assert response.json()['results']['bindings'][0]['concat']['value'] == "Firstlast"


def test_concat_construct_xml():
    # expected to return turtle
    response = endpoint.post(
        "/",
        data="query=" + label_construct,
        headers={"accept": "application/xml"},
    )
    assert response.status_code == 200


def test_bad_request():
    response = endpoint.get("/?query=figarofigarofigaro", headers={"accept": "application/json"})
    assert response.status_code == 400


label_select = """PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?label WHERE {
    ?s rdfs:label ?label .
}"""


label_construct = """PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
CONSTRUCT {
    <http://test> <http://label> ?label .
} WHERE {
    ?s rdfs:label ?label .
}"""
