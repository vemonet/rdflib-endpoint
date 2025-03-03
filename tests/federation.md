# Federated query to rdflib-endpoint

To test it locally start the docker compose stack in this folder

## Test locally

Need to use the host from the docker network:

```sparql
SELECT * WHERE {
  SERVICE <http://rdflib-endpoint/> {
      SELECT ?o WHERE {
        ?s ?p ?o .
      }
    }
}
```

Local with FILTER:

```SPARQL
SELECT * WHERE {
  SERVICE <http://rdflib-endpoint/> {
      SELECT ?o WHERE {
        VALUES ?s { <http://subject> }
        ?s ?p ?o .
      }
    }
}
```

Test on bioregistry simple:

```SPARQL
PREFIX owl: <http://www.w3.org/2002/07/owl#>
SELECT * WHERE {
  SERVICE <https://bioregistry.io/sparql> {
      <http://purl.obolibrary.org/obo/CHEBI_1> owl:sameAs ?o
    }
}
```

Test on bioregistry with values:

```SPARQL
PREFIX owl: <http://www.w3.org/2002/07/owl#>
SELECT * WHERE {
  SERVICE <https://bioregistry.io/sparql> {
      VALUES ?s { <http://purl.obolibrary.org/obo/CHEBI_1> }
      ?s owl:sameAs ?o
    }
}
```

## ✅ Working

- Qlever: https://qlever.cs.uni-freiburg.de/uniprot/
- Virtuoso: if not using VALUES in service call
- Oxigraph
- GraphDB (fixed at last release)
- Blazegraph
- Fuseki

## ❌ Not working

- MilleniumDB
