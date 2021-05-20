import rdflib
from rdflib.plugins.sparql.evaluate import evalPart
from rdflib.plugins.sparql.sparql import SPARQLError
from rdflib.plugins.sparql.evalutils import _eval
from rdflib.namespace import Namespace
from rdflib.term import Literal

from openpredict_classifier import query_classifier_from_sparql
# Import for custom function calculation
# from Levenshtein import distance as levenshtein_distance # python-Levenshtein==0.12.2



def SPARQL_openpredict(ctx:object, part:object) -> object:
    """
    Retrieve variables from a SPARQL-query, then get predictions
    The score value is then stored in Literal object and added to the query results.
    
    Example:

    Query:
        PREFIX custom: <//custom/>

        SELECT ?label1 ?label2 ?prediction WHERE {
          BIND("Hello" AS ?label1)
          BIND("World" AS ?label2)
          BIND(custom:openpredict(?label1, ?label2) AS ?prediction)
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
    namespace = Namespace('//custom/')
    openpredict = rdflib.term.URIRef(namespace + 'openpredict')

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

                # Here it checks if it can find our levenshtein IRI (example: //custom/levenshtein)
                # Please note that IRI and URI are almost the same.
                # Earlier this has been defined with the following:
                    # namespace = Namespace('//custom/')
                    # levenshtein = rdflib.term.URIRef(namespace + 'levenshtein')

                if part.expr.iri == openpredict:

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


# namespace = Namespace('//custom/')
# openpredict = rdflib.term.URIRef(namespace + 'openpredict')


# query = """
# PREFIX custom: <%s>

# SELECT ?label1 ?label2 ?openpredict WHERE {
#   BIND("Hello" AS ?label1)
#   BIND("World" AS ?label2)
#   BIND(custom:openpredict(?label1, ?label2) AS ?openpredict)
# }
# """ % (namespace,)

# # Save custom function in custom evaluation dictionary.
# rdflib.plugins.sparql.CUSTOM_EVALS['SPARQL_openpredict'] = SPARQL_openpredict


# for row in rdflib.Graph().query(query):
#     print(row)