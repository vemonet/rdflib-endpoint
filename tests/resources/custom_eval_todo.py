import rdflib
from fastapi.testclient import TestClient
from rdflib import URIRef
from rdflib.namespace import RDF, RDFS
from rdflib.plugins.sparql.evaluate import evalBGP

from rdflib_endpoint import SparqlEndpoint

# TODO: not used due to bug with FastAPI TestClient when using different apps in the tests


def custom_eval(ctx, part):
    """Rewrite triple patterns to get super-classes"""
    if part.name == "BGP":
        # rewrite triples
        triples = []
        for t in part.triples:
            if t[1] == RDF.type:
                bnode = rdflib.BNode()
                triples.append((t[0], t[1], bnode))
                triples.append((bnode, RDFS.subClassOf, t[2]))
            else:
                triples.append(t)
        # delegate to normal evalBGP
        return evalBGP(ctx, triples)
    raise NotImplementedError()


g = rdflib.Graph()
g.add((URIRef("http://human"), RDFS.subClassOf, URIRef("http://mammal")))
g.add((URIRef("http://alice"), RDF.type, URIRef("http://human")))

eval_app = SparqlEndpoint(graph=g, custom_eval=custom_eval, functions={})
eval_endpoint = TestClient(eval_app)


def test_custom_eval():
    # eval_app = SparqlEndpoint(
    #     graph=g,
    #     custom_eval=custom_eval,
    #     functions={}
    # )
    # eval_endpoint = TestClient(eval_app)

    response = eval_endpoint.get("/sparql?query=" + select_parent, headers={"accept": "application/json"})
    print(response.json())
    assert response.status_code == 200
    print(response.json()["results"]["bindings"])
    assert str(response.json()["results"]["bindings"][0]["s"]["value"]) == "http://alice"

    response = eval_endpoint.post("/sparql", data="query=" + select_parent, headers={"accept": "application/json"})
    assert response.status_code == 200
    assert str(response.json()["results"]["bindings"][0]["s"]["value"]) == "http://alice"


select_parent = """SELECT * WHERE {
    ?s a <http://mammal> .
}"""
