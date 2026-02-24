# Example SPARQL endpoint for Python function

A SPARQL endpoint with custom functions implemented in Python.

> Built with [RDFLib](https://github.com/RDFLib/rdflib) and [FastAPI](https://fastapi.tiangolo.com/), CORS enabled.

## ✨️ Run

> Requirements: [`uv`](https://docs.astral.sh/uv/getting-started/installation/) to easily handle scripts and virtual environments.

Run the server on http://localhost:8000

```sh
uv run uvicorn main:app --reload
```

## 🐳 Run with docker

Checkout the `Dockerfile` to see how the image is built, and run it with the `compose.yml`:

```sh
docker compose up --build
```

## 🧩 Features

> [!NOTE]
>
> Docs auto-generated from function docstring and signature with:
>
> ```sh
> uv run example/gen_docs.py
> ```

<!-- FUNCTIONS_START -->

### `func:StringSplitter`

Split a string and return each part with their index.

**IRI:** `urn:sparql-function:StringSplitter`

**Inputs:**

| Predicate | Type | Default | Description |
|-----------------|------|---------|-------------|
| `func:splitString` | `str` | *required* | The string to split. |
| `func:separator` | `str` | `' '` | The character to split on. |

**Outputs:**

| Predicate | Type | Description |
|----------------------|------|-------------|
| `func:splitted` | `str` | The part of the string that was split out. |
| `func:index` | `int` | The zero-based index of the part in the original string. |

**Example:**

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


### `func:UriSplitter`

Split a URI and return each part with their index.

**IRI:** `urn:sparql-function:UriSplitter`

**Inputs:**

| Predicate | Type | Default | Description |
|-----------------|------|---------|-------------|
| `func:splitString` | `URIRef` | *required* | The URI to split. |
| `func:separator` | `str` | `'/'` | The character to split on. |

**Outputs:**

| Predicate | Type | Description |
|----------------------|------|-------------|
| `func:splitted` | `str` | The part of the string that was split out. |
| `func:index` | `int` | The zero-based index of the part in the original string. |

**Example:**

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


### `owl:sameAs`

Get all alternative IRIs for a given IRI using the Bioregistry.

**IRI:** `http://www.w3.org/2002/07/owl#sameAs`

**Subject input:** `input_iri` (`URIRef`) — The input IRI to find alternative identifiers for.

**Object output:** `owl:sameAs` (`list[URIRef]`) — A list of alternative IRIs from all known providers.

**Example:**

```sparql
PREFIX owl: <http://www.w3.org/2002/07/owl#>
SELECT ?sameAs WHERE {
    <https://identifiers.org/CHEBI/1> owl:sameAs ?sameAs .
}
```


### `dc:identifier`

Get the standardized IRI for a given input IRI.

**IRI:** `http://purl.org/dc/elements/1.1/identifier`

**Subject input:** `input_iri` (`URIRef`) — The input IRI to standardize.

**Object output:** `dc:identifier` (`URIRef`) — The standardized canonical IRI.

**Example:**

```sparql
PREFIX dc: <http://purl.org/dc/elements/1.1/>
SELECT ?id WHERE {
    <https://identifiers.org/CHEBI/1> dc:identifier ?id .
}
```


### `func:split`

Split a string into parts.

**IRI:** `urn:sparql-function:split`

**Inputs:**

| Arguments | Type | Default | Description |
|-----------------|------|---------|-------------|
| `input_str` | `str` | *required* | The string to split. |
| `separator` | `str` | `' '` | The character to split on. |

**Outputs:**

| Variables | Type | Description |
|----------------------|------|-------------|
| `?var` | `list[str]` | A list of string parts. |

**Example:**

```sparql
PREFIX func: <urn:sparql-function:>
SELECT ?input ?part WHERE {
    VALUES ?input { "hello world" "cheese is good" }
    BIND(func:split(?input, " ") AS ?part)
}
```


### `func:splitIndex`

Split a string and return each part with their index.

**IRI:** `urn:sparql-function:splitIndex`

**Inputs:**

| Arguments | Type | Default | Description |
|-----------------|------|---------|-------------|
| `input_str` | `str` | *required* | The string to split. |
| `separator` | `str` | `' '` | The character to split on. |

**Outputs:**

| Variables | Type | Description |
|----------------------|------|-------------|
| `?var` | `str` | The part of the string that was split out. |
| `?varIndex` | `int` | The zero-based index of the part in the original string. |

**Example:**

```sparql
PREFIX func: <urn:sparql-function:>
SELECT ?input ?part ?partIndex WHERE {
    VALUES ?input { "hello world" "cheese is good" }
    BIND(func:splitIndex(?input, " ") AS ?part)
}
```


### `func:splitGraph`

Split a string and return the results as an RDF graph.

**IRI:** `urn:sparql-function:splitGraph`

**Inputs:**

| Predicate | Type | Default | Description |
|-----------------|------|---------|-------------|
| `input_str` | `str` | *required* | The string to split. |
| `separator` | `str` | `' '` | The character to split on. |

**Output:** `?g` (`Graph`) — An RDFLib Graph with a triple per part, using `func:splitting` as the subject and `func:splitted` as the predicate.

**Example:**

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


### `sparqlfunction:joinStr`

Join two strings with an optional separator.

**IRI:** `urn:sparql-function:joinStr`

**Inputs:**

| Arguments | Type | Default | Description |
|-----------------|------|---------|-------------|
| `input_str` | `str` | *required* | The string to echo. |
| `separator` | `Union[str, NoneType]` | `None` | An optional separator to append. |

**Outputs:**

| Variables | Type | Description |
|----------------------|------|-------------|
| `?var` | `str` |  |

<!-- FUNCTIONS_END -->
