from openpredict.rdf_utils import OPENPREDICT
import rdflib
from rdflib.plugins.sparql.evaluate import evalPart, evalBGP
from rdflib.plugins.sparql.sparql import SPARQLError
from rdflib.plugins.sparql.evalutils import _eval
from rdflib.namespace import Namespace
from rdflib.term import Literal

from openpredict_classifier import query_classifier_from_sparql, query_openpredict_classifier

def SPARQL_resolve_patterns(ctx:object, part:object) -> object:
    """
    Retrieve variables from a SPARQL-query, then get predictions
    The score value is then stored in Literal object and added to the query results.
    
    Example:

    Query:
        PREFIX openpredict: <https://w3id.org/um/openpredict/>
        PREFIX biolink: <https://w3id.org/biolink/vocab/>
        SELECT ?drugOrDisease ?predictedForTreatment ?score WHERE {
            ?association a rdf:Statement ;
                rdf:subject ?drugOrDisease ;
                rdf:object ?predictedForTreatment ;
                rdf:predicate ?predicate ;
                biolink:category biolink:ChemicalToDiseaseOrPhenotypicFeatureAssociation ;
                biolink:has_confidence_level ?score .
            BIND("OMIM:246300" AS ?drugOrDisease)
            BIND(openpredict:prediction(?drugOrDisease) AS ?predictedForTreatment)
        }
    
    Problem with this query: requires to run the classifier for all entities
    VALUES ?predicate { biolink:treats|biolink:treated_by }

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
    OPENPREDICT = Namespace('https://w3id.org/um/openpredict/')
    BIOLINK = Namespace('https://w3id.org/biolink/vocab/')
    openpredict_similarity_uri = OPENPREDICT['prediction']

    print('SPARQL query part:')
    print(part.name)

    if part.name == 'Extend':
        print('The part.expr:')
        print(part.expr)

    if part.name == "BGP":

        # rewrite triples
        triples = []
        for t in part.triples:
            print('The triples:')
            print(t)
            # if t[1] == rdflib.RDF.type:
            #     bnode = rdflib.BNode()
            #     triples.append((t[0], t[1], bnode))
            #     triples.append((bnode, inferredSubClass, t[2]))
            # else:
            triples.append(t)

        # delegate to normal evalBGP
        return evalBGP(ctx, triples)

    raise NotImplementedError()



def SPARQL_openpredict_prediction(ctx:object, part:object) -> object:
    """
    Retrieve variables from a SPARQL-query, then get predictions
    The score value is then stored in Literal object and added to the query results.
    
    Example:

    Query:
        PREFIX openpredict: <https://w3id.org/um/openpredict/>
        SELECT ?drugOrDisease ?predictedForTreatment ?openpredictScore WHERE {
            BIND("OMIM:246300" AS ?drugOrDisease)
            BIND(openpredict:prediction(?drugOrDisease) AS ?predictedForTreatment)
        }

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
                    scores = []
                    for prediction in predictions_list:
                        # Quick fix to get results for drugs or diseases
                        if argument1.startswith('OMIM') or argument1.startswith('MONDO'):
                            evaluation.append(prediction['drug'])
                        else:
                            evaluation.append(prediction['disease'])
                        scores.append(prediction['score'])

                    # evaluation = [Literal(argument1 + argument2), Literal(argument2 + argument1)]
                else:
                    # When other function used  
                    evaluation = []
    # Standard error handling and return statements
                # else:
                #     raise SPARQLError('Unhandled function {}'.format(part.expr.iri))
            else:
                evaluation = [_eval(part.expr, c.forget(ctx, _except=part._vars))]
                scores = []
                if isinstance(evaluation[0], SPARQLError):
                    raise evaluation[0]
            for i, result in enumerate(evaluation):
            # for result in evaluation:
                print('evaluation and scores')
                print(evaluation)
                print(scores)
                if len(scores) < i+1:
                    cs.append(c.merge({part.var: Literal(result)}))
                else:
                    print(part.var)
                    # cs.append(c.merge({part.var: Literal(result), 'openpredictScore': Literal(scores[i])}))
                    cs.append(c.merge({part.var: Literal(result)}))
                    cs.append(c.merge({'openpredictScore': Literal(scores[i])}))
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
