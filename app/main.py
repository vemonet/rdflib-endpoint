import rdflib
from rdflib import Graph, Literal, RDF, URIRef
from rdflib.plugins.sparql.evaluate import evalPart, evalBGP
from rdflib.plugins.sparql.evalutils import _eval
from rdflib import Graph, Literal, RDF, URIRef
from rdflib.namespace import Namespace

from openpredict.openpredict_model import query_omim_drugbank_classifier
from openpredict.openpredict_utils import init_openpredict_dir

from sparql_endpoint import SparqlEndpoint

# EvalBGP https://rdflib.readthedocs.io/en/stable/_modules/rdflib/plugins/sparql/evaluate.html
# Custom fct for rdf:type with auto infer super-classes: https://github.com/RDFLib/rdflib/blob/master/examples/custom_eval.py
# BGP = Basic Graph Pattern
# Docs rdflib custom fct: https://rdflib.readthedocs.io/en/stable/intro_to_sparql.html
# StackOverflow: https://stackoverflow.com/questions/43976691/custom-sparql-functions-in-rdflib/66988421#66988421

# Another project: https://github.com/bas-stringer/scry/blob/master/query_handler.py
# https://www.w3.org/TR/sparql11-service-description/#example-turtle
# Federated query: https://www.w3.org/TR/2013/REC-sparql11-federated-query-20130321/#defn_service
# XML method: https://rdflib.readthedocs.io/en/stable/apidocs/rdflib.plugins.sparql.results.html#module-rdflib.plugins.sparql.results.xmlresults


def most_similar(query_results, ctx, part, eval_part):
    """
    Get most similar entities for a given entity

    Query:
    PREFIX openpredict: <https://w3id.org/um/openpredict/>
    SELECT ?drugOrDisease ?mostSimilar ?mostSimilarScore WHERE {
        BIND("OMIM:246300" AS ?drugOrDisease)
        BIND(openpredict:most_similar(?drugOrDisease) AS ?mostSimilar)
    """
    argument1 = str(_eval(part.expr.expr[0], eval_part.forget(ctx, _except=part.expr._vars)))
    argument2 = str(_eval(part.expr.expr[1], eval_part.forget(ctx, _except=part.expr._vars)))
    
    similarity_results = {}
    # TODO: get similarity from dataframe
    
    evaluation = []
    scores = []
    for most_similar in similarity_results:
        # Quick fix to get results for drugs or diseases
        # evaluation.append(most_similar['entity'])
        # scores.append(most_similar['score'])
        evaluation.append(str(argument1) + str(argument2))

    # Append the results for our custom function
    for i, result in enumerate(evaluation):
        query_results.append(eval_part.merge({
            part.var: Literal(result), 
            # rdflib.term.Variable(part.var + 'Score'): Literal(scores[i])
        }))
    return query_results, ctx, part, eval_part


def get_predictions(query_results, ctx, part, eval_part):
    """
    Query OpenPredict classifier to get drug/disease predictions

    Query:
    PREFIX openpredict: <https://w3id.org/um/openpredict/>
    SELECT ?drugOrDisease ?predictedForTreatment ?predictedForTreatmentScore WHERE {
        BIND("OMIM:246300" AS ?drugOrDisease)
        BIND(openpredict:prediction(?drugOrDisease) AS ?predictedForTreatment)
    """
    argument1 = str(_eval(part.expr.expr[0], eval_part.forget(ctx, _except=part.expr._vars)))

    # Run the classifier to get predictions and scores for the entity given as argument
    predictions_list = query_omim_drugbank_classifier(argument1, 'openpredict-baseline-omim-drugbank')

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
        query_results.append(eval_part.merge({
            part.var: Literal(result), 
            rdflib.term.Variable(part.var + 'Score'): Literal(scores[i])
        }))
    return query_results, ctx, part, eval_part


def custom_concat(query_results, ctx, part, eval_part):
    """
    Concat 2 string and return the length as additional Length variable

    Query:
    PREFIX myfunctions: <https://w3id.org/um/sparql-functions/>
    SELECT ?concat ?concatLength WHERE {
        BIND("First" AS ?first)
        BIND(myfunctions:custom_concat(?first, "last") AS ?concat)
    }
    """
    argument1 = str(_eval(part.expr.expr[0], eval_part.forget(ctx, _except=part.expr._vars)))
    argument2 = str(_eval(part.expr.expr[1], eval_part.forget(ctx, _except=part.expr._vars)))
    evaluation = []
    scores = []

    concat_string = argument1 + argument2
    evaluation.append(concat_string)
    scores.append(len(concat_string))
    # Append the results for our custom function
    for i, result in enumerate(evaluation):
        query_results.append(eval_part.merge({
            part.var: Literal(result), 
            rdflib.term.Variable(part.var + 'Length'): Literal(scores[i])
        }))
    return query_results, ctx, part, eval_part


init_openpredict_dir()
# Start the SPARQL endpoint based on a RDFLib Graph
g = Graph()
app = SparqlEndpoint(
    graph=g,
    functions={
        'https://w3id.org/um/openpredict/prediction': get_predictions,
        'https://w3id.org/um/openpredict/most_similar': most_similar,
        'https://w3id.org/um/sparql-functions/custom_concat': custom_concat
    },
    title="SPARQL endpoint for RDFLib graph", 
    description="A SPARQL endpoint to serve machine learning models, or any other logic implemented in Python. \n[Source code](https://github.com/vemonet/rdflib-endpoint)",
    version="0.0.1",
    cors_enabled=True
)
