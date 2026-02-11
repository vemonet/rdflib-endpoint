from dataclasses import dataclass
from typing import List

import bioregistry
from rdflib import DC, OWL, XSD, Graph, Literal, Namespace, URIRef

from rdflib_endpoint import DatasetExt

# ds = DatasetExt(default_union=True)
ds = DatasetExt()
FUNC = Namespace("https://w3id.org/sparql-functions/")


@dataclass
class SplitterResult:
    splitted: str
    index: int


# Type pattern function
@ds.type_function()
def string_splitter(
    split_string: str,
    separator: str = " ",
) -> List[SplitterResult]:
    """Split a string and return each part with their index."""
    split = split_string.split(separator)
    return [SplitterResult(splitted=part, index=idx) for idx, part in enumerate(split)]


@ds.type_function()
def uri_splitter(
    split_string: URIRef,
    separator: str = "/",
) -> List[SplitterResult]:
    """Split a string and return each part with their index."""
    split = split_string.split(separator)
    return [SplitterResult(splitted=part, index=idx) for idx, part in enumerate(split)]


# Predicate function
conv = bioregistry.get_converter()


@ds.predicate_function(namespace=OWL._NS)
def same_as(input_iri: URIRef) -> List[URIRef]:
    """Get all alternative IRIs for a given IRI using the Bioregistry."""
    prefix, identifier = conv.compress(input_iri).split(":", 1)
    return [URIRef(iri) for iri in bioregistry.get_providers(prefix, identifier).values()]


@ds.predicate_function(namespace=DC._NS)
def identifier(input_iri: URIRef) -> URIRef:
    """Get the standardized IRI for a given input IRI."""
    return URIRef(conv.standardize_uri(input_iri))


# Extension function with single output
@ds.extension_function()
def split(
    input_str: str,
    separator: str = " ",
) -> List[str]:
    """Split a string."""
    return input_str.split(separator)


# Extension function with outputs to multiple variables
@dataclass
class SplitResult:
    splitted: str
    index: int


@ds.extension_function()
def split_index(
    input_str: str,
    separator: str = " ",
) -> List[SplitResult]:
    """Split a string and return each part with their index."""
    split = input_str.split(separator)
    return [SplitResult(splitted=part, index=idx) for idx, part in enumerate(split)]


@ds.graph_function()
def split_graph(
    input_str: str,
    separator: str = " ",
) -> Graph:
    """Split a string and return the results in a graph."""
    g = Graph()
    for part in input_str.split(separator):
        g.add((FUNC.splitting, FUNC.splitted, Literal(part)))
    return g


expected_with_index = [
    (Literal("hello world"), Literal("hello"), Literal("0", datatype=XSD.integer)),
    (Literal("hello world"), Literal("world"), Literal("1", datatype=XSD.integer)),
    (Literal("cheese is good"), Literal("cheese"), Literal("0", datatype=XSD.integer)),
    (Literal("cheese is good"), Literal("is"), Literal("1", datatype=XSD.integer)),
    (Literal("cheese is good"), Literal("good"), Literal("2", datatype=XSD.integer)),
]


def test_extension_function_multi_output() -> None:
    query = """PREFIX func: <https://w3id.org/sparql-functions/>
    SELECT ?input ?part ?partIndex WHERE {
        VALUES ?input { "hello world" "cheese is good" }
        BIND(func:splitIndex(?input, " ") AS ?part)
    }"""
    assert list(ds.query(query)) == expected_with_index

    # With default separator
    query_default_sep = """PREFIX func: <https://w3id.org/sparql-functions/>
    SELECT ?input ?part ?partIndex WHERE {
        VALUES ?input { "hello world" "cheese is good" }
        BIND(func:splitIndex(?input) AS ?part)
    }"""
    assert list(ds.query(query_default_sep)) == expected_with_index


def test_extension_function_single_output() -> None:
    expected = [
        (Literal("hello world"), Literal("hello"), None),
        (Literal("hello world"), Literal("world"), None),
        (Literal("cheese is good"), Literal("cheese"), None),
        (Literal("cheese is good"), Literal("is"), None),
        (Literal("cheese is good"), Literal("good"), None),
    ]
    query = """PREFIX func: <https://w3id.org/sparql-functions/>
    SELECT ?input ?part ?partIndex WHERE {
        VALUES ?input { "hello world" "cheese is good" }
        BIND(func:split(?input, " ") AS ?part)
    }"""
    assert list(ds.query(query)) == expected

    # With default separator
    query_default_sep = """PREFIX func: <https://w3id.org/sparql-functions/>
    SELECT ?input ?part ?partIndex WHERE {
        VALUES ?input { "hello world" "cheese is good" }
        BIND(func:split(?input) AS ?part)
    }"""
    assert list(ds.query(query_default_sep)) == expected


def test_pattern_function() -> None:
    query = """PREFIX func: <https://w3id.org/sparql-functions/>
    SELECT ?input ?part ?idx WHERE {
        VALUES ?input { "hello world" "cheese is good" }
        [] a func:StringSplitter ;
            func:splitString ?input ;
            func:separator " " ;
            func:splitted ?part ;
            func:index ?idx .
    }"""
    assert list(ds.query(query)) == expected_with_index

    # With default separator
    query_default_sep = """PREFIX func: <https://w3id.org/sparql-functions/>
    SELECT ?input ?part ?idx WHERE {
        VALUES ?input { "hello world" "cheese is good" }
        [] a func:StringSplitter ;
            func:splitString ?input ;
            func:splitted ?part ;
            func:index ?idx .
    }"""
    assert list(ds.query(query_default_sep)) == expected_with_index


def test_graph_function() -> None:
    expected = [
        (FUNC["graph/split_graph"], FUNC["splitting"], FUNC["splitted"], Literal("cheese")),
        (FUNC["graph/split_graph"], FUNC["splitting"], FUNC["splitted"], Literal("is")),
        (FUNC["graph/split_graph"], FUNC["splitting"], FUNC["splitted"], Literal("good")),
        (FUNC["graph/split_graph"], FUNC["splitting"], FUNC["splitted"], Literal("hello")),
        (FUNC["graph/split_graph"], FUNC["splitting"], FUNC["splitted"], Literal("world")),
    ]
    query = """PREFIX func: <https://w3id.org/sparql-functions/>
    SELECT ?g ?s ?p ?o WHERE {
        VALUES ?input { "hello world" "cheese is good" }
        BIND(func:splitGraph(?input, " ") AS ?g)
        GRAPH ?g {
            ?s ?p ?o .
        }
    }"""
    for row in ds.query(query):
        assert row in expected

    # With default separator
    query_default_sep = """PREFIX func: <https://w3id.org/sparql-functions/>
    SELECT ?g ?s ?p ?o WHERE {
        VALUES ?input { "hello world" "cheese is good" }
        BIND(func:splitGraph(?input) AS ?g)
        GRAPH ?g {
            ?s ?p ?o .
        }
    }"""
    for row in ds.query(query_default_sep):
        assert row in expected


def test_predicate_function_identifier() -> None:
    query = """PREFIX dc: <http://purl.org/dc/elements/1.1/>
    SELECT ?id WHERE {
        <https://identifiers.org/CHEBI/1> dc:identifier ?id .
    }"""
    expected = (URIRef("http://purl.obolibrary.org/obo/CHEBI_1"),)
    assert list(ds.query(query)) == [expected]


def test_predicate_function_same_as() -> None:
    query = """PREFIX owl: <http://www.w3.org/2002/07/owl#>
    SELECT ?sameAs WHERE {
        <https://identifiers.org/CHEBI/1> owl:sameAs ?sameAs .
    }"""
    result = list(ds.query(query))
    print(result)
    assert len(result) > 5


def test_multiple_functions_combined() -> None:
    query = """PREFIX dc: <http://purl.org/dc/elements/1.1/>
    PREFIX func: <https://w3id.org/sparql-functions/>
    SELECT ?splitted WHERE {
        <https://identifiers.org/CHEBI/1> dc:identifier ?id .
        BIND(func:split(?id, "_") AS ?part)
        [] a func:StringSplitter ;
            func:splitString ?part ;
            func:separator "." ;
            func:splitted ?splitted ;
            func:index ?idx .
    }"""
    split_res = [str(row[0]) for row in ds.query(query)]
    # print(split_res)
    assert "http://purl" in split_res
    assert "obolibrary" in split_res
    assert "org/obo/CHEBI" in split_res
    assert "1" in split_res


def test_type_function_uri_input() -> None:
    query = """PREFIX dc: <http://purl.org/dc/elements/1.1/>
    PREFIX func: <https://w3id.org/sparql-functions/>
    SELECT ?splitted WHERE {
        [] a func:UriSplitter ;
            func:splitString <http://purl.org/dc/elements/1.1/> ;
            func:separator "/" ;
            func:splitted ?splitted ;
            func:index ?idx .
    }"""
    split_res = [str(row[0]) for row in ds.query(query)]
    print(split_res)
    # assert "http://purl" in split_res
    # assert "obolibrary" in split_res
    # assert "org/obo/CHEBI" in split_res
    # assert "1" in split_res
