import rdflib
from rdflib.plugins.sparql.evaluate import evalPart
from rdflib.plugins.sparql.sparql import SPARQLError
from rdflib.plugins.sparql.evalutils import _eval
from rdflib.namespace import Namespace
from rdflib.term import Literal

from openpredict_classifier import query_classifier_from_sparql

# Docs rdflib custom fct: https://rdflib.readthedocs.io/en/stable/intro_to_sparql.html
# StackOverflow: https://stackoverflow.com/questions/43976691/custom-sparql-functions-in-rdflib/66988421#66988421
# Another project: https://github.com/bas-stringer/scry/blob/master/query_handler.py

def SPARQL_openpredict_similarity(ctx:object, part:object) -> object:
    """
    Retrieve variables from a SPARQL-query, then get predictions
    The score value is then stored in Literal object and added to the query results.
    
    Example:

    Query:
        PREFIX custom: <https://w3id.org/um/openpredict/>

        SELECT ?label1 ?label2 ?prediction WHERE {
          BIND("Hello" AS ?label1)
          BIND("World" AS ?label2)
          BIND(openpredict:similarity(?label1, ?label2) AS ?prediction)
        }

    Retrieve:
        ?label1 ?label2

    Calculation:
        prediction(?label1, ?label2) =  score

    Output:
        Save score in Literal object.

    :param ctx:     <class 'rdflib.plugins.sparql.sparql.QueryContext'>
    :param part:    <class 'rdflib.plugins.sparql.parserutils.CompValue'>
    :return:        <class 'rdflib.plugins.sparql.processor.SPARQLResult'>
    """
    namespace = Namespace('https://w3id.org/um/openpredict/')
    openpredict_similarity_uri = rdflib.term.URIRef(namespace + 'similarity')

    # This part holds basic implementation for adding new functions
    if part.name == 'Extend':
        cs = []

        # Information is retrieved and stored and passed through a generator
        for c in evalPart(ctx, part.p):

            # Checks if the function holds an internationalized resource identifier
            # This will check if any custom functions are added.
            if hasattr(part.expr, 'iri'):

                # From here the real calculations begin.
                # First we get the variable arguments, for example ?label1 and ?label2
                argument1 = str(_eval(part.expr.expr[0], c.forget(ctx, _except=part.expr._vars)))
                argument2 = str(_eval(part.expr.expr[1], c.forget(ctx, _except=part.expr._vars)))

                # Here it checks if it can find our levenshtein IRI (example: https://w3id.org/um/openpredict/levenshtein)
                # Please note that IRI and URI are almost the same.
                # Earlier this has been defined with the following:
                    # namespace = Namespace('https://w3id.org/um/openpredict/')
                    # levenshtein = rdflib.term.URIRef(namespace + 'levenshtein')

                if part.expr.iri == openpredict_similarity_uri:

                    # After finding the correct path for the custom SPARQL function the evaluation can begin.
                    # Here the levenshtein distance is calculated using ?label1 and ?label2 and stored as an Literal object.
                    # This object is than stored as an output value of the SPARQL-query (example: ?levenshtein)
                    # evaluation = Literal(levenshtein_distance(argument1, argument2))
                    evaluation = Literal(argument1 + argument2)
                    # predictions_list = query_classifier_from_sparql(parsed_query)


    # Standard error handling and return statements
                else:
                    raise SPARQLError('Unhandled function {}'.format(part.expr.iri))
            else:
                evaluation = _eval(part.expr, c.forget(ctx, _except=part._vars))
                if isinstance(evaluation, SPARQLError):
                    raise evaluation
            cs.append(c.merge({part.var: evaluation}))
        return cs
    raise NotImplementedError()

