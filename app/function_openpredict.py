import rdflib
from rdflib.plugins.sparql.evaluate import evalPart
from rdflib.plugins.sparql.sparql import SPARQLError
from rdflib.plugins.sparql.evalutils import _eval
from rdflib.namespace import Namespace
from rdflib.term import Literal

from openpredict_classifier import query_classifier_from_sparql, query_openpredict_classifier


def SPARQL_openpredict_prediction(ctx:object, part:object) -> object:
    """
    Retrieve variables from a SPARQL-query, then get predictions
    The score value is then stored in Literal object and added to the query results.
    
    Example:

    Query:
        PREFIX openpredict: <https://w3id.org/um/openpredict/>
        SELECT ?drugOrDisease ?predictedForTreatment WHERE {
          BIND("OMIM:246300" AS ?drugOrDisease)
          BIND(openpredict:prediction(?drugOrDisease) AS ?predictedForTreatment)
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
    openpredict_similarity_uri = rdflib.term.URIRef(namespace + 'prediction')

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
                # argument2 = str(_eval(part.expr.expr[1], c.forget(ctx, _except=part.expr._vars)))

                # Here it checks if it can find our levenshtein IRI (example: https://w3id.org/um/openpredict/levenshtein)
                # Please note that IRI and URI are almost the same.
                # Earlier this has been defined with the following:
                    # namespace = Namespace('https://w3id.org/um/openpredict/')
                    # levenshtein = rdflib.term.URIRef(namespace + 'levenshtein')

                if part.expr.iri == openpredict_similarity_uri:

                    # After finding the correct path for the custom SPARQL function the evaluation can begin.
                    # Here the levenshtein distance is calculated using ?label1 and ?label2 and stored as an Literal object.
                    # This object is than stored as an output value of the SPARQL-query (example: ?levenshtein)
                    # evaluation = Literal(argument1 + argument2)
                    predictions_list = query_openpredict_classifier(argument1)
                    evaluation = []
                    for prediction in predictions_list:
                        # Quick fix to get results for drugs or diseases
                        if argument1.startswith('OMIM') or argument1.startswith('MONDO'):
                            evaluation.append(prediction['drug'])
                        else:
                            evaluation.append(prediction['disease'])
                        # evaluation.append(prediction['score'])

                    # evaluation = [Literal(argument1 + argument2), Literal(argument2 + argument1)]
                else:
                    # When other function used  
                    evaluation = []
    # Standard error handling and return statements
                # else:
                #     raise SPARQLError('Unhandled function {}'.format(part.expr.iri))
            else:
                evaluation = [_eval(part.expr, c.forget(ctx, _except=part._vars))]
                if isinstance(evaluation[0], SPARQLError):
                    raise evaluation[0]
            for result in evaluation:
                cs.append(c.merge({part.var: Literal(result)}))
        return cs
    raise NotImplementedError()
    

def SPARQL_openpredict_similarity(ctx:object, part:object) -> object:
    """
    Retrieve variables from a SPARQL-query, then get predictions
    The score value is then stored in Literal object and added to the query results.
    
    Example:

    Query:
        PREFIX openpredict: <https://w3id.org/um/openpredict/>

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
                if len(part.expr.expr) > 1:
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
                    # evaluation = Literal(argument1 + argument2)
                    evaluation = [Literal(argument1 + argument2), Literal(argument2 + argument1)]
                    # predictions_list = query_classifier_from_sparql(parsed_query)
                else:
                    # When other function used  
                    evaluation = []

    # Standard error handling and return statements
                # else:
                #     raise SPARQLError('Unhandled function {}'.format(part.expr.iri))
            else:
                evaluation = [_eval(part.expr, c.forget(ctx, _except=part._vars))]
                if isinstance(evaluation[0], SPARQLError):
                    raise evaluation[0]
            for result in evaluation:
                cs.append(c.merge({part.var: result}))
        return cs
    raise NotImplementedError()
