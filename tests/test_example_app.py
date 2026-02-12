from example.main import app
from fastapi.testclient import TestClient
from rdflib import Graph

from rdflib_endpoint.sparql_router import SD

# Use app defined in example folder
endpoint = TestClient(app)


def test_service_description():
    # Check GET turtle
    response = endpoint.get("/", headers={"accept": "text/turtle"})
    print(response.text)
    assert response.status_code == 200
    g = Graph()
    g.parse(data=response.text, format="turtle")
    assert any(g.triples((None, SD.endpoint, None))), "Missing sd:endpoint in service description"
    assert any(g.triples((None, SD.extensionFunction, None))), "Missing sd:extensionFunction in service description"
    assert len(list(g.triples((None, SD.extensionFunction, None)))) >= 2, "Expected at least 2 extension functions"
    assert len(list(g.triples((None, SD.namedGraph, None)))) >= 2, "Expected at least 2 named graphs"

    # Check POST turtle
    response = endpoint.post("/", headers={"accept": "text/turtle"})
    assert response.status_code == 200
    g = Graph()
    g.parse(data=response.text, format="turtle")
    assert any(g.triples((None, SD.endpoint, None))), "Missing sd:endpoint in service description"
    assert any(g.triples((None, SD.extensionFunction, None))), "Missing sd:extensionFunction in service description"
    assert len(list(g.triples((None, SD.extensionFunction, None)))) >= 2, "Expected at least 2 extension functions"

    # Check POST XML
    response = endpoint.post("/", headers={"accept": "application/xml"})
    assert response.status_code == 200
    g = Graph()
    g.parse(data=response.text, format="xml")
    assert any(g.triples((None, SD.endpoint, None))), "Missing sd:endpoint in service description"
    assert any(g.triples((None, SD.extensionFunction, None))), "Missing sd:extensionFunction in service description"
    assert len(list(g.triples((None, SD.extensionFunction, None)))) >= 2, "Expected at least 2 extension functions"


def test_custom_concat():
    response = endpoint.get("/", params={"query": custom_function_query}, headers={"accept": "application/json"})
    # print(response.json())
    assert response.status_code == 200
    assert response.json()["results"]["bindings"][0]["part"]["value"] == "hello"

    response = endpoint.post(
        "/",
        data={"query": custom_function_query},
        headers={"accept": "application/json"},
    )
    assert response.status_code == 200
    assert response.json()["results"]["bindings"][0]["part"]["value"] == "hello"


def test_bad_request():
    response = endpoint.get("/?query=figarofigarofigaro", headers={"accept": "application/json"})
    assert response.status_code == 400


custom_function_query = """PREFIX func: <urn:sparql-function:>
SELECT ?input ?part ?partIndex WHERE {
    VALUES ?input { "hello world" "cheese is good" }
    BIND(func:splitIndex(?input, " ") AS ?part)
}"""
