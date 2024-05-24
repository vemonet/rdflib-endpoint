import pytest
from example.app.main import custom_concat
from fastapi.testclient import TestClient
from rdflib import RDFS, Graph, Literal, URIRef

from rdflib_endpoint import SparqlEndpoint

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
        "https://w3id.org/um/sparql-functions/custom_concat": custom_concat,
    },
    enable_update=True,
)

endpoint = TestClient(app)


def test_service_description():
    response = endpoint.get("/", headers={"accept": "text/turtle"})
    assert response.status_code == 200
    assert response.text.strip() == service_description

    response = endpoint.post("/", headers={"accept": "text/turtle"})
    assert response.status_code == 200
    assert response.text.strip() == service_description

    # Check for application/xml
    response = endpoint.post("/", headers={"accept": "application/xml"})
    assert response.status_code == 200


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


def test_fail_select_turtle():
    response = endpoint.post("/", data={"query": concat_select}, headers={"accept": "text/turtle"})
    assert response.status_code == 422


def test_concat_construct_turtle():
    response = endpoint.post(
        "/",
        data={"query": custom_concat_construct},
        headers={"accept": "text/turtle"},
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


concat_select = """PREFIX myfunctions: <https://w3id.org/um/sparql-functions/>
SELECT ?concat ?concatLength WHERE {
    BIND("First" AS ?first)
    BIND(myfunctions:custom_concat(?first, "last") AS ?concat)
}"""

custom_concat_construct = """PREFIX myfunctions: <https://w3id.org/um/sparql-functions/>
CONSTRUCT {
    <http://example.com/test> <http://example.com/concat> ?concat, ?concatLength .
} WHERE {
    BIND("First" AS ?first)
    BIND(myfunctions:custom_concat(?first, "last") AS ?concat)
}"""

service_description = """@prefix dc: <http://purl.org/dc/elements/1.1/> .
@prefix ent: <http://www.w3.org/ns/entailment/> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix sd: <http://www.w3.org/ns/sparql-service-description#> .

<https://w3id.org/um/sparql-functions/custom_concat> a sd:Function .

<https://your-endpoint/sparql> a sd:Service ;
    rdfs:label "SPARQL endpoint for RDFLib graph" ;
    dc:description "A SPARQL endpoint to serve machine learning models, or any other logic implemented in Python. [Source code](https://github.com/vemonet/rdflib-endpoint)" ;
    sd:defaultDataset [ a sd:Dataset ;
            sd:defaultGraph [ a sd:Graph ] ] ;
    sd:defaultEntailmentRegime ent:RDFS ;
    sd:endpoint <https://your-endpoint/sparql> ;
    sd:extensionFunction <https://w3id.org/um/sparql-functions/custom_concat> ;
    sd:feature sd:DereferencesURIs ;
    sd:resultFormat <http://www.w3.org/ns/formats/SPARQL_Results_CSV>,
        <http://www.w3.org/ns/formats/SPARQL_Results_JSON> ;
    sd:supportedLanguage sd:SPARQL11Query ."""
