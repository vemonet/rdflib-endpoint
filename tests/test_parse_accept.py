import pytest

import rdflib_endpoint.sparql_router

accept_cases = [
    ("text/xml", "text/xml"),
    ("text/rdf+xml, text/xml, */*", "text/rdf+xml"),
    ("text/html, application/xhtml+xml, application/xml;q=0.9, */*;q=0.8", "text/html"),
    ("text/html;q=0.3, application/xhtml+xml, application/xml;q=0.9, */*;q=0.8", "application/xhtml+xml"),
    (
        'text/turtle;q=0.9;profile="urn:example:profile-1", text/turtle;q=0.7;profile="urn:example:profile-2"',
        "text/turtle",
    ),
]


@pytest.mark.parametrize("accept,expected", accept_cases)
def test_accept_preference(accept, expected):
    pref = rdflib_endpoint.sparql_router.parse_accept_header(accept)
    assert pref[0] == expected
