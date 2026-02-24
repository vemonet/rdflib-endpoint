from dataclasses import dataclass
from typing import List, Optional

import bioregistry
from rdflib import DC, OWL, RDF, RDFS, Graph, Literal, Namespace, URIRef

from rdflib_endpoint import DatasetExt, SparqlEndpoint

ds = DatasetExt(
    # store="Oxigraph",
    default_union=True,
)
FUNC = Namespace("urn:sparql-function:")


@dataclass
class SplitterResult:
    splitted: str
    """The part of the string that was split out."""
    index: int
    """The zero-based index of the part in the original string."""


# NOTE: add sparql codeblocks in docstrings with example on how to use the functions,
# these will be extracted and added as YASGUI queries tabs


# Type pattern function
@ds.type_function()
def string_splitter(
    split_string: str,
    separator: str = " ",
) -> List[SplitterResult]:
    """Split a string and return each part with their index.

    Args:
        split_string: The string to split.
        separator: The character to split on.

    Example:
        ```sparql
        PREFIX func: <urn:sparql-function:>
        SELECT ?input ?part ?idx
        WHERE {
            VALUES ?input { "hello world" "cheese is good" }
            [] a func:StringSplitter ;
                func:splitString ?input ;
                func:separator " " ;
                func:splitted ?part ;
                func:index ?idx .
        }
        ```
    """
    split = split_string.split(separator)
    return [SplitterResult(splitted=part, index=idx) for idx, part in enumerate(split)]


@ds.type_function()
def uri_splitter(
    split_string: URIRef,
    separator: str = "/",
) -> List[SplitterResult]:
    """Split a URI and return each part with their index.

    Args:
        split_string: The URI to split.
        separator: The character to split on.

    Example:
        ```sparql
        PREFIX func: <urn:sparql-function:>
        SELECT ?input ?part ?idx
        WHERE {
            VALUES ?input { "hello world" "cheese is good" }
            [] a func:UriSplitter ;
                func:splitString ?input ;
                func:separator " " ;
                func:splitted ?part ;
                func:index ?idx .
        }
        ```
    """
    split = split_string.split(separator)
    return [SplitterResult(splitted=part, index=idx) for idx, part in enumerate(split)]


# Predicate function
conv = bioregistry.get_converter()


@ds.predicate_function(namespace=OWL._NS)
def same_as(input_iri: URIRef) -> List[URIRef]:
    """Get all alternative IRIs for a given IRI using the Bioregistry.

    Args:
        input_iri (URIRef): The input IRI to find alternative identifiers for.

    Returns:
        List[URIRef]: A list of alternative IRIs from all known providers.

    Example:
        ```sparql
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        SELECT ?sameAs WHERE {
            <https://identifiers.org/CHEBI/1> owl:sameAs ?sameAs .
        }
        ```
    """
    prefix, identifier = conv.compress(input_iri).split(":", 1)
    return [URIRef(iri) for iri in bioregistry.get_providers(prefix, identifier).values()]


@ds.predicate_function(namespace=DC._NS)
def identifier(input_iri: URIRef) -> URIRef:
    """Get the standardized IRI for a given input IRI.

    Args:
        input_iri (URIRef): The input IRI to standardize.

    Returns:
        URIRef: The standardized canonical IRI.

    Example:
        ```sparql
        PREFIX dc: <http://purl.org/dc/elements/1.1/>
        SELECT ?id WHERE {
            <https://identifiers.org/CHEBI/1> dc:identifier ?id .
        }
        ```
    """
    return URIRef(conv.standardize_uri(input_iri))


# Extension function with single output
@ds.extension_function()
def split(
    input_str: str,
    separator: str = " ",
) -> List[str]:
    """Split a string into parts.

    Args:
        input_str: The string to split.
        separator: The character to split on.

    Returns:
        List[str]: A list of string parts.

    Example:
        ```sparql
        PREFIX func: <urn:sparql-function:>
        SELECT ?input ?part WHERE {
            VALUES ?input { "hello world" "cheese is good" }
            BIND(func:split(?input, " ") AS ?part)
        }
        ```
    """
    return input_str.split(separator)


# Extension function with outputs to multiple variables
@dataclass
class SplitResult:
    splitted: str
    """The part of the string that was split out."""
    index: int
    """The zero-based index of the part in the original string."""


@ds.extension_function()
def split_index(
    input_str: str,
    separator: str = " ",
) -> List[SplitResult]:
    """Split a string and return each part with their index.

    Args:
        input_str: The string to split.
        separator: The character to split on.

    Returns:
        List[SplitResult]: A list of results containing each part and its zero-based index.

    Example:
        ```sparql
        PREFIX func: <urn:sparql-function:>
        SELECT ?input ?part ?partIndex WHERE {
            VALUES ?input { "hello world" "cheese is good" }
            BIND(func:splitIndex(?input, " ") AS ?part)
        }
        ```
    """
    split = input_str.split(separator)
    return [SplitResult(splitted=part, index=idx) for idx, part in enumerate(split)]


@ds.graph_function()
def split_graph(
    input_str: str,
    separator: str = " ",
) -> Graph:
    """Split a string and return the results as an RDF graph.

    Args:
        input_str: The string to split.
        separator: The character to split on.

    Returns:
        Graph: An RDFLib Graph with a triple per part, using `func:splitting` as
            the subject and `func:splitted` as the predicate.

    Example:
        ```sparql
        PREFIX func: <urn:sparql-function:>
        SELECT * WHERE {
            VALUES ?input { "hello world" "cheese is good" }
            BIND(func:splitGraph(?input, " ") AS ?g)
            GRAPH ?g {
                ?s ?p ?o .
            }
        }
        ```
    """
    g = Graph()
    for part in input_str.split(separator):
        g.add((FUNC.splitting, FUNC.splitted, Literal(part)))
    return g


# Function whose namespace has no example to exercise _get_ns_prefix fallback
# and Optional[str] parameter to exercise _annotation_to_str origin branch in gen_docs..
@ds.extension_function(namespace=FUNC)
def join_str(
    input_str: str,
    separator: Optional[str] = None,
) -> str:
    """Join two strings with an optional separator.

    Args:
        input_str: The string to echo.
        separator: An optional separator to append.
    """
    if separator is None:
        return input_str
    return input_str + separator


# You can also direcrtly add triples to the dataset graphs
ds.graph(URIRef("http://graph1")).add((URIRef("http://subject"), RDF.type, URIRef("http://object")))
ds.graph(URIRef("http://graph2")).add((URIRef("http://subject"), RDFS.label, Literal("foo")))

# Start the SPARQL endpoint based on the RDFLib Graph
app = SparqlEndpoint(
    graph=ds,
    title="SPARQL endpoint for RDFLib graph",
    description="A SPARQL endpoint to serve any logic implemented in Python. \n[Source code](https://github.com/vemonet/rdflib-endpoint)",
    version="0.1.0",
    path="/",
    public_url="http://127.0.0.1:8000/",
    cors_enabled=True,
    enable_update=True,
)

## Uncomment to run it directly with python app/main.py
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)
