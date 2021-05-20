from rdflib_web.lod import lod
import Flask
import rdflib
from function_openpredict import SPARQL_openpredict

# Installation not working...

# python3 app/rdflib_web.py
# https://github.com/RDFLib/rdflib-web
# https://github.com/RDFLib/rdflib-web/blob/master/rdflib_web/generic_endpoint.py
# https://rdflib-web.readthedocs.io/en/latest/#

app = Flask(__name__)

rdflib.plugins.sparql.CUSTOM_EVALS['SPARQL_openpredict'] = SPARQL_openpredict

graph = rdflib.Graph()

app.config['graph'] = graph
app.register_blueprint(lod)

