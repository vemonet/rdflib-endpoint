from openpredict.rdf_utils import OPENPREDICT
import rdflib
from rdflib.plugins.sparql.evaluate import evalPart, evalBGP
from rdflib.plugins.sparql.sparql import SPARQLError
from rdflib.plugins.sparql.evalutils import _eval

from rdflib.namespace import Namespace
from rdflib.term import Literal

from openpredict_classifier import query_openpredict_classifier


def SPARQL_custom_functions(ctx:object, part:object) -> object:
    """
    Retrieve variables from a SPARQL-query, then get predictions
    The score value is then stored in Literal object and added to the query results.
    
    Example:

    Query:
        PREFIX openpredict: <https://w3id.org/um/openpredict/>
        SELECT ?drugOrDisease ?predictedForTreatment ?predictedForTreatmentScore WHERE {
            BIND("OMIM:246300" AS ?drugOrDisease)
            BIND(openpredict:prediction(?drugOrDisease) AS ?predictedForTreatment)
        }

        BIND(openpredict:score(?drugOrDisease) AS ?predictedForTreatment)
        https://github.com/w3c/sparql-12/issues/6

    Problem with this query: how to retrieve the ?score ? We just add it to the results?

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

    # This part holds basic implementation for adding new functions
    if part.name == 'Extend':
        query_results = []

        # Information is retrieved and stored and passed through a generator
        for c in evalPart(ctx, part.p):
            # Checks if the function is a URI (custom function)
            if hasattr(part.expr, 'iri'):
                OPENPREDICT = Namespace('https://w3id.org/um/openpredict/')

                ## Implementation of the function starts here
                # We check if the function URI is the same as our function
                # same as rdflib.term.URIRef('https://w3id.org/um/openpredict/prediction')
                if part.expr.iri == OPENPREDICT['prediction']:
                    argument1 = str(_eval(part.expr.expr[0], c.forget(ctx, _except=part.expr._vars)))

                    # Run the classifier to get predictions and scores for the entity given as argument
                    predictions_list = query_openpredict_classifier(argument1)
                    evaluation = []
                    scores = []
                    for prediction in predictions_list:
                        # Quick fix to get results for drugs or diseases
                        if argument1.startswith('OMIM') or argument1.startswith('MONDO'):
                            evaluation.append(prediction['drug'])
                        else:
                            evaluation.append(prediction['disease'])
                        scores.append(prediction['score'])
                    # Append the results for our custom function
                    for i, result in enumerate(evaluation):
                        query_results.append(c.merge({
                            part.var: Literal(result), 
                            rdflib.term.Variable(part.var + 'Score'): Literal(scores[i])
                        }))


                ## TODO: Add a new function such as most_similar
                elif part.expr.iri == OPENPREDICT['most_similar']:
                    argument1 = str(_eval(part.expr.expr[0], c.forget(ctx, _except=part.expr._vars)))
                    argument2 = str(_eval(part.expr.expr[1], c.forget(ctx, _except=part.expr._vars)))
                    
                    similarity_results = {}
                    # TODO: get similarity from dataframe
                    
                    evaluation = []
                    scores = []
                    for most_similar in similarity_results:
                        # Quick fix to get results for drugs or diseases
                        evaluation.append(most_similar['entity'])
                        scores.append(most_similar['score'])

                    # Append the results for our custom function
                    for i, result in enumerate(evaluation):
                        query_results.append(c.merge({
                            part.var: Literal(result), 
                            rdflib.term.Variable(part.var + 'Score'): Literal(scores[i])
                        }))


                # Handling when function not registered
                else:
                    raise SPARQLError('Unhandled function {}'.format(part.expr.iri))
            else:
                # For built-in SPARQL functions (that are not URIs)
                evaluation = [_eval(part.expr, c.forget(ctx, _except=part._vars))]
                # scores = [_eval(part.expr, c.forget(ctx, _except={rdflib.term.Variable('openpredictScore')}))]
                # scores = []
                if isinstance(evaluation[0], SPARQLError):
                    raise evaluation[0]
                # Append results for built-in SPARQL functions
                for result in evaluation:
                    query_results.append(c.merge({part.var: Literal(result)}))
                    
        # print(query_results)
        return query_results
    raise NotImplementedError()

