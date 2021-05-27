from fastapi.testclient import TestClient
from example.app.main import app

endpoint = TestClient(app)

def test_service_description():
    response = endpoint.get('/sparql', headers={'accept': 'text/turtle'})
    assert response.status_code == 200
    assert response.text.strip() == service_description

    response = endpoint.post('/sparql', 
        headers={'accept': 'text/turtle'})
    assert response.status_code == 200
    assert response.text.strip() == service_description


def test_custom_concat():
    response = endpoint.get('/sparql?query=' + custom_concat_query, 
        headers={'accept': 'application/json'})
    assert response.status_code == 200
    assert response.json()['results']['bindings'][0]['concat']['value'] == "Firstlast"

    response = endpoint.post('/sparql', 
        data='query=' + custom_concat_query, 
        headers={'accept': 'application/json'})
    assert response.status_code == 200
    assert response.json()['results']['bindings'][0]['concat']['value'] == "Firstlast"


custom_concat_query = """PREFIX myfunctions: <https://w3id.org/um/sparql-functions/>
SELECT ?concat ?concatLength WHERE {
    BIND("First" AS ?first)
    BIND(myfunctions:custom_concat(?first, "last") AS ?concat)
}"""


service_description = """@prefix ent: <http://www.w3.org/ns/entailment/> .
@prefix sd: <http://www.w3.org/ns/sparql-service-description#> .

<https://w3id.org/um/openpredict/most_similar> a sd:Function .

<https://w3id.org/um/openpredict/prediction> a sd:Function .

<https://w3id.org/um/sparql-functions/custom_concat> a sd:Function .

[] a sd:Service ;
    sd:defaultDataset [ a sd:Dataset ;
            sd:defaultGraph [ a sd:Graph ] ] ;
    sd:defaultEntailmentRegime ent:RDFS ;
    sd:endpoint <https://sparql-openpredict.137.120.31.102.nip.io/sparql> ;
    sd:extensionFunction <https://w3id.org/um/openpredict/similarity> ;
    sd:feature sd:DereferencesURIs ;
    sd:resultFormat <http://www.w3.org/ns/formats/SPARQL_Results_CSV>,
        <http://www.w3.org/ns/formats/SPARQL_Results_JSON> ;
    sd:supportedLanguage sd:SPARQL11Query ."""
