from example.main import app, ds
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


def test_generate_docs():
    """generate_docs() should return non-empty Markdown covering registered functions."""

    docs = ds.generate_docs(verbose=True)
    assert docs, "generate_docs() returned empty string"

    # All registered functions should appear by name (ignore prefixes)
    for meta in ds._custom_functions.values():
        assert meta.func.__name__.lower().replace("_", "") in docs.lower(), (
            f"{meta.func.__name__} missing from generated docs"
        )

    # Each function type label should appear
    for label in ("type function", "predicate function", "extension function", "graph function"):
        assert label in docs, f"decorator type '{label}' missing from generated docs"

    # Every doc section should include an IRI line
    assert "**IRI:**" in docs
    # Docstring descriptions should be extracted
    assert "Split a string" in docs
    # type_function param names use prefixed predicate IRIs (func:splitString)
    assert "func:splitString" in docs
    # predicate_function params still use the Python name (subject input)
    assert "input_iri" in docs
    # Outputs section must be present
    assert "**Outputs:**" in docs
    # extension_function binds to ?var
    assert "?var" in docs
    # graph_function binds to ?g
    assert "?g" in docs
    # SPARQL examples should be included
    assert "```sparql" in docs
    # _annotation_to_str origin branch: Optional[str] renders as Union[str, None] or similar
    assert "Optional" in docs or "Union" in docs or "str" in docs
    # _get_ns_prefix fallback: namespace http://example.org/ext/ -> prefix "ext"
    assert "sparqlfunction:joinStr" in docs
