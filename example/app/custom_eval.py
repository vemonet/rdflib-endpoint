"""
This example shows how a custom evaluation function can be added to
handle certain SPARQL Algebra elements.

A custom function is added that adds ``rdfs:subClassOf`` "inference" when
asking for ``rdf:type`` triples.

Here the custom eval function is added manually, normally you would use
setuptools and entry_points to do it:
i.e. in your setup.py::

    entry_points = {
        'rdf.plugins.sparqleval': [
            'myfunc =     mypackage:MyFunction',
            ],
    }
"""

# EvalBGP https://rdflib.readthedocs.io/en/stable/_modules/rdflib/plugins/sparql/evaluate.html
# Custom fct for rdf:type with auto infer super-classes: https://github.com/RDFLib/rdflib/blob/master/examples/custom_eval.py
# BGP = Basic Graph Pattern
# Docs rdflib custom fct: https://rdflib.readthedocs.io/en/stable/intro_to_sparql.html
# StackOverflow: https://stackoverflow.com/questions/43976691/custom-sparql-functions-in-rdflib/66988421#66988421

# Another project: https://github.com/bas-stringer/scry/blob/master/query_handler.py
# https://www.w3.org/TR/sparql11-service-description/#example-turtle
# Federated query: https://www.w3.org/TR/2013/REC-sparql11-federated-query-20130321/#defn_service
# XML method: https://rdflib.readthedocs.io/en/stable/apidocs/rdflib.plugins.sparql.results.html#module-rdflib.plugins.sparql.results.xmlresults

import rdflib
from rdflib import BNode, Literal, URIRef, Variable
from rdflib.namespace import FOAF
from rdflib.plugins.sparql import parser
from rdflib.plugins.sparql.algebra import pprintAlgebra, translateQuery
from rdflib.plugins.sparql.evaluate import evalBGP, evalPart
from rdflib.plugins.sparql.evalutils import _eval
from rdflib.plugins.sparql.parserutils import Expr
from rdflib.plugins.sparql.sparql import Prologue, Query

inferredSubClass = rdflib.RDFS.subClassOf * "*"  # any number of rdfs.subClassOf
biolink = URIRef("https://w3id.org/biolink/vocab/")

class Result:
        pass

def addToGraph(ctx, drug, disease, score):
    bnode = rdflib.BNode()
    ctx.graph.add((bnode, rdflib.RDF.type, rdflib.RDF.Statement))
    ctx.graph.add((bnode, rdflib.RDF.subject, drug))
    ctx.graph.add((bnode, rdflib.RDF.predicate, biolink + 'treats'))
    ctx.graph.add((bnode, rdflib.RDF.object, disease))
    ctx.graph.add((bnode, biolink + 'category', biolink + 'ChemicalToDiseaseOrPhenotypicFeatureAssociation'))
    ctx.graph.add((bnode, biolink + 'has_confidence_level', score))

def getTriples(disease):
    drug = URIRef("http://bio2rdf.org/drugbank:DB00001")
    score = Literal("1.0")

    r = Result()
    r.drug = drug
    r.disease = disease
    r.score = score
    
    results = []
    results.append(r)
    return results

#def parseRelationalExpr(expr):


def customEval(ctx, part):
    """
    
    """
    #print (part.name)

    if part.name == "Project":
        ctx.myvars = []
    
    # search extend for variable binding
    if part.name == 'Extend':
        if hasattr(part, "expr"):
            if not isinstance(part.expr, list):
                ctx.myvars.append(part.expr)

    # search for filter
    if part.name == "Filter":
        if hasattr(part,"expr"):
            if hasattr(part.expr, "expr"):
                if part.expr.expr['op'] == '=':
                    e = part.expr.expr['expr']
                    d = part.expr.expr['other']
                    ctx.myvars.append(d)
            else:
                if part.expr['op'] == '=':
                    e = part.expr['expr']
                    d = part.expr['other']
                    ctx.myvars.append(d)

    # search the BGP for the variable of interest
    if part.name == "BGP":
        triples = []
        for t in part.triples:
            if t[1] == rdflib.RDF.object:
                disease = t[2]
                # check first if the disease term is specified in the bgp triple
                if(isinstance(disease, rdflib.term.URIRef)):
                    ctx.myvars.append(disease)
                
                # fetch instances
                for d in ctx.myvars:
                    results = getTriples(d)
                    for r in results:
                        addToGraph(ctx, r.drug, r.disease, r.score)
            
            triples.append(t)
        return evalBGP(ctx, triples)
    raise NotImplementedError()


if __name__ == "__main__":

    # add function directly, normally we would use setuptools and entry_points
    rdflib.plugins.sparql.CUSTOM_EVALS["exampleEval"] = customEval

    g = rdflib.Graph()

    q = '''PREFIX openpredict: <https://w3id.org/um/openpredict/>
        PREFIX biolink: <https://w3id.org/biolink/vocab/>
        PREFIX omim: <http://bio2rdf.org/omim:>
        SELECT ?disease ?drug ?score 
        {
            ?association a rdf:Statement ;
                rdf:subject ?drug ;
                rdf:predicate ?predicate ;
                #rdf:object omim:246300 ;
                rdf:object ?disease ;
                biolink:category biolink:ChemicalToDiseaseOrPhenotypicFeatureAssociation ;
                biolink:has_confidence_level ?score .
            #?disease dcat:identifier "OMIM:246300" .
            BIND(omim:1 AS ?disease)
            #FILTER(?disease = omim:2 || ?disease = omim:3)
            #VALUES ?disease { omim:5 omim:6 omim:7 }
        }'''

    pq = parser.parseQuery(q)
    tq = translateQuery(pq)
    pprintAlgebra(tq)

    # Find all FOAF Agents
    for x in g.query(q):
        print(x)
