import urllib.parse

from fastapi.testclient import TestClient
from rdflib import RDF, RDFS, Graph, Literal, URIRef

from rdflib_endpoint import SparqlEndpoint

g = Graph(store="Oxigraph")
g.add((URIRef("http://subject"), RDF.type, URIRef("http://object")))
g.add((URIRef("http://subject"), RDFS.label, Literal("test value")))


app = SparqlEndpoint(graph=g)

endpoint = TestClient(app)


def test_service_description():
    response = endpoint.get("/sparql", headers={"accept": "text/turtle"})
    assert response.status_code == 200
    # assert response.text.strip() == service_description

    response = endpoint.post("/sparql", headers={"accept": "text/turtle"})
    assert response.status_code == 200
    # assert response.text.strip() == service_description

    # Check for application/xml
    response = endpoint.post("/sparql", headers={"accept": "application/xml"})
    assert response.status_code == 200


def test_custom_concat_json():
    response = endpoint.get("/sparql?query=" + urllib.parse.quote(label_select), headers={"accept": "application/json"})
    # print(response.json())
    assert response.status_code == 200
    assert response.json()["results"]["bindings"][0]["label"]["value"] == "test value"

    response = endpoint.post("/sparql", data="query=" + label_select, headers={"accept": "application/json"})
    assert response.status_code == 200
    assert response.json()["results"]["bindings"][0]["label"]["value"] == "test value"


def test_select_noaccept_xml():
    response = endpoint.post("/sparql", data="query=" + label_select)
    assert response.status_code == 200
    # assert response.json()['results']['bindings'][0]['concat']['value'] == "Firstlast"


def test_select_csv():
    response = endpoint.post("/sparql", data="query=" + label_select, headers={"accept": "text/csv"})
    assert response.status_code == 200
    # assert response.json()['results']['bindings'][0]['concat']['value'] == "Firstlast"


def test_fail_select_turtle():
    response = endpoint.post("/sparql", data="query=" + label_select, headers={"accept": "text/turtle"})
    assert response.status_code == 422
    # assert response.json()['results']['bindings'][0]['concat']['value'] == "Firstlast"


def test_concat_construct_turtle():
    # expected to return turtle
    response = endpoint.post(
        "/sparql",
        data="query=" + label_construct,
        headers={"accept": "application/json"},
    )
    assert response.status_code == 200
    # assert response.json()['results']['bindings'][0]['concat']['value'] == "Firstlast"


def test_concat_construct_xml():
    # expected to return turtle
    response = endpoint.post(
        "/sparql",
        data="query=" + label_construct,
        headers={"accept": "application/xml"},
    )
    assert response.status_code == 200


def test_bad_request():
    response = endpoint.get("/sparql?query=figarofigarofigaro", headers={"accept": "application/json"})
    assert response.status_code == 400


def test_redirect():
    response = endpoint.get("/")
    assert response.status_code == 200


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

# service_description = """@prefix dc: <http://purl.org/dc/elements/1.1/> .
# @prefix ent: <http://www.w3.org/ns/entailment/> .
# @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
# @prefix sd: <http://www.w3.org/ns/sparql-service-description#> .

# <https://sparql.openpredict.semanticscience.org/sparql> a sd:Service ;
#     rdfs:label "SPARQL endpoint for RDFLib graph" ;
#     dc:description "A SPARQL endpoint to serve machine learning models, or any other logic implemented in Python. [Source code](https://github.com/vemonet/rdflib-endpoint)" ;
#     sd:defaultDataset [ a sd:Dataset ;
#             sd:defaultGraph [ a sd:Graph ] ] ;
#     sd:defaultEntailmentRegime ent:RDFS ;
#     sd:endpoint <https://sparql.openpredict.semanticscience.org/sparql> ;
#     sd:extensionFunction <https://w3id.org/um/sparql-functions/custom_concat> ;
#     sd:feature sd:DereferencesURIs ;
#     sd:resultFormat <http://www.w3.org/ns/formats/SPARQL_Results_CSV>,
#         <http://www.w3.org/ns/formats/SPARQL_Results_JSON> ;
#     sd:supportedLanguage sd:SPARQL11Query .

# <https://w3id.org/um/sparql-functions/custom_concat> a sd:Function ."""
