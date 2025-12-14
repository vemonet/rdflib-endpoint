from typing import Any, Dict, List, Optional, TypedDict, Union

from rdflib import Namespace

SD = Namespace("http://www.w3.org/ns/sparql-service-description#")
FORMATS = Namespace("http://www.w3.org/ns/formats/")


class Defaults:
    """Default configuration values for the SPARQL endpoint."""

    title: str = "SPARQL endpoint for RDFLib graph"
    description: str = "A SPARQL endpoint to serve machine learning models, or any other logic implemented in Python. \n[Source code](https://github.com/vemonet/rdflib-endpoint)"
    version: str = "0.1.0"
    public_url: str = "https://your-endpoint/sparql"
    favicon: str = "https://rdflib.readthedocs.io/en/stable/_static/RDFlib.png"
    example: str = """\
PREFIX myfunctions: <https://w3id.org/sparql-functions/>

SELECT ?concat ?concatLength WHERE {
    BIND("First" AS ?first)
    BIND(myfunctions:custom_concat(?first, "last") AS ?concat)
}
""".rstrip()
    #: This is default for federated queries
    content_type: str = "application/xml"


API_RESPONSES: Optional[Dict[Union[int, str], Dict[str, Any]]] = {
    200: {
        "description": "SPARQL query results",
        "content": {
            "application/sparql-results+json": {"example": {"results": {"bindings": []}, "head": {"vars": []}}},
            "application/json": {"example": {"results": {"bindings": []}, "head": {"vars": []}}},
            "text/csv": {"example": "s,p,o"},
            "application/sparql-results+csv": {"example": "s,p,o"},
            "application/sparql-results+xml": {"example": "<root></root>"},
            "application/xml": {"example": "<root></root>"},
            "text/turtle": {"example": "<http://subject> <http://predicate> <http://object> ."},
            "application/n-triples": {"example": "<http://subject> <http://predicate> <http://object> ."},
            "text/n3": {"example": "<http://subject> <http://predicate> <http://object> ."},
            "application/n-quads": {"example": "<http://subject> <http://predicate> <http://object> <http://graph> ."},
            "application/trig": {
                "example": "GRAPH <http://graph> {<http://subject> <http://predicate> <http://object> .}"
            },
            "application/trix": {"example": "<xml></xml>"},
            "application/ld+json": {
                "example": [
                    {
                        "@id": "http://subject",
                        "@type": ["http://object"],
                        "http://www.w3.org/2000/01/rdf-schema#label": [{"@value": "foo"}],
                    }
                ]
            },
            # "application/rdf+xml": {
            #     "example": '<?xml version="1.0" encoding="UTF-8"?> <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"></rdf:RDF>'
            # },
        },
    },
    400: {
        "description": "Bad Request",
    },
    403: {
        "description": "Forbidden",
    },
    422: {
        "description": "Unprocessable Entity",
    },
}

#: A mapping from content types to the keys used for serializing
#: in :meth:`rdflib.Graph.serialize` and other serialization functions
GRAPH_CONTENT_TYPE_TO_RDFLIB_FORMAT = {
    # https://www.w3.org/TR/rdf-sparql-XMLres/
    "application/rdf+xml": "xml",  # for compatibility
    "application/ld+json": "json-ld",
    # https://www.w3.org/TR/sparql11-results-csv-tsv/
    # Extras
    "text/turtle": "ttl",
    "text/n3": "n3",
    "application/n-triples": "nt",
    "text/plain": "nt",
    "application/trig": "trig",
    "application/trix": "trix",
    "application/n-quads": "nquads",
}

SPARQL_RESULT_CONTENT_TYPE_TO_RDFLIB_FORMAT = {
    # https://www.w3.org/TR/sparql11-results-json/
    "application/sparql-results+json": "json",
    # https://www.w3.org/TR/rdf-sparql-XMLres/
    "application/sparql-results+xml": "xml",
    # https://www.w3.org/TR/sparql11-results-csv-tsv/
    "application/sparql-results+csv": "csv",
}

GENERIC_CONTENT_TYPE_TO_RDFLIB_FORMAT = {
    # https://www.w3.org/TR/sparql11-results-json/
    "application/json": "json",
    "text/json": "json",
    # https://www.w3.org/TR/rdf-sparql-XMLres/
    "application/xml": "xml",  # for compatibility
    "text/xml": "xml",  # not standard
    # https://www.w3.org/TR/sparql11-results-csv-tsv/
    "text/csv": "csv",  # for compatibility
}


def parse_accept_header(accept: str) -> List[str]:
    """Given an accept header string, return a list of media types in order of preference.

    :param accept: Accept header value
    :return: Ordered list of media type preferences
    """

    def _parse_preference(qpref: str) -> float:
        qparts = qpref.split("=")
        try:
            return float(qparts[1].strip())
        except (ValueError, IndexError):
            pass
        return 1.0

    preferences = []
    types = accept.split(",")
    dpref = 2.0
    for mtype in types:
        parts = mtype.split(";")
        parts = [part.strip() for part in parts]
        pref = dpref
        try:
            for part in parts[1:]:
                if part.startswith("q="):
                    pref = _parse_preference(part)
                    break
        except IndexError:
            pass
        # preserve order of appearance in the list
        dpref = dpref - 0.01
        preferences.append((parts[0], pref))
    preferences.sort(key=lambda x: -x[1])
    return [pref[0] for pref in preferences]


class QueryExample(TypedDict, total=False):
    """Dictionary to store example queries for the SPARQL endpoint."""

    query: str
    endpoint: Optional[str]
