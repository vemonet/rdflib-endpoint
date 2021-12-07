from fastapi.testclient import TestClient
from rdflib_endpoint import SparqlEndpoint
from example.app.main import custom_concat

# Use app defined in example folder
app = SparqlEndpoint(
    functions={
        'https://w3id.org/um/sparql-functions/custom_concat': custom_concat,
    }
)

endpoint = TestClient(app)

def test_service_description():
    response = endpoint.get('/sparql', headers={'accept': 'text/turtle'})
    print(response.text.strip())
    assert response.status_code == 200
    assert response.text.strip() == service_description

    response = endpoint.post('/sparql', 
        headers={'accept': 'text/turtle'})
    assert response.status_code == 200
    assert response.text.strip() == service_description

    # Check for application/xml
    response = endpoint.post('/sparql', 
        headers={'accept': 'application/xml'})
    assert response.status_code == 200


def test_custom_concat_json():
    response = endpoint.get('/sparql?query=' + custom_concat_query, 
        headers={'accept': 'application/json'})
    # print(response.json())
    assert response.status_code == 200
    assert response.json()['results']['bindings'][0]['concat']['value'] == "Firstlast"

    response = endpoint.post('/sparql', 
        data='query=' + custom_concat_query, 
        headers={'accept': 'application/json'})
    assert response.status_code == 200
    assert response.json()['results']['bindings'][0]['concat']['value'] == "Firstlast"

def test_custom_concat_xml():
    response = endpoint.post('/sparql', 
        data='query=' + custom_concat_query, 
        headers={'accept': 'application/xml'})
    assert response.status_code == 200
    # assert response.json()['results']['bindings'][0]['concat']['value'] == "Firstlast"

def test_custom_concat_turtle():
    response = endpoint.post('/sparql', 
        data='query=' + custom_concat_query, 
        headers={'accept': 'text/turtle'})
    assert response.status_code == 200
    # assert response.json()['results']['bindings'][0]['concat']['value'] == "Firstlast"

def test_bad_request():
    response = endpoint.get('/sparql?query=figarofigarofigaro', 
        headers={'accept': 'application/json'})
    assert response.status_code == 400

def test_redirect():
    response = endpoint.get('/')
    assert response.status_code == 200


custom_concat_query = """PREFIX myfunctions: <https://w3id.org/um/sparql-functions/>
SELECT ?concat ?concatLength WHERE {
    BIND("First" AS ?first)
    BIND(myfunctions:custom_concat(?first, "last") AS ?concat)
}"""

service_description = """@prefix dc: <http://purl.org/dc/elements/1.1/> .
@prefix ent: <http://www.w3.org/ns/entailment/> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix sd: <http://www.w3.org/ns/sparql-service-description#> .

<https://sparql.openpredict.semanticscience.org/sparql> a sd:Service ;
    rdfs:label "SPARQL endpoint for RDFLib graph" ;
    dc:description "A SPARQL endpoint to serve machine learning models, or any other logic implemented in Python. [Source code](https://github.com/vemonet/rdflib-endpoint)" ;
    sd:defaultDataset [ a sd:Dataset ;
            sd:defaultGraph [ a sd:Graph ] ] ;
    sd:defaultEntailmentRegime ent:RDFS ;
    sd:endpoint <https://sparql.openpredict.semanticscience.org/sparql> ;
    sd:extensionFunction <https://w3id.org/um/sparql-functions/custom_concat> ;
    sd:feature sd:DereferencesURIs ;
    sd:resultFormat <http://www.w3.org/ns/formats/SPARQL_Results_CSV>,
        <http://www.w3.org/ns/formats/SPARQL_Results_JSON> ;
    sd:supportedLanguage sd:SPARQL11Query .

<https://w3id.org/um/sparql-functions/custom_concat> a sd:Function ."""
