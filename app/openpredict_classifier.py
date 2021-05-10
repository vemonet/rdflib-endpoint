import numpy as np
import pandas as pd
import re
from joblib import dump, load
from rdflib import Graph, Literal, RDF, URIRef, Namespace
import pathlib

pathlib.Path(__file__).parent.absolute()

def get_dir(path=''):
    """Return the full path to the provided files in the OpenPredict data folder
    Where models and features for runs are stored
    """
    return str(pathlib.Path(__file__).parent.absolute()) + "/" + path

def query_classifier_from_sparql(parsed_query):
    predictions_list = []
    for triple in parsed_query.algebra.p.p.triples:
        if str(triple[1]).endswith('://w3id.org/biolink/vocab/treats') or str(triple[1]).endswith('://w3id.org/biolink/vocab/treated_by'):
        # if predicate is treats then we get the entities to search
            curie_to_predict = None
            curie_to_predict2 = None

            # if triple[0].startswith('http://') or triple[0].startswith('https://'):
            if isinstance(triple[0], URIRef):
                curie_to_predict = str(triple[0]).replace('https://identifiers.org/', '')
            
            # if triple[2].startswith('http://') or triple[0].startswith('https://'):
            if isinstance(triple[2], URIRef):
                if curie_to_predict:
                    curie_to_predict2 = str(triple[2]).replace('https://identifiers.org/', '')
                else:
                    curie_to_predict = str(triple[2]).replace('https://identifiers.org/', '')
            predictions_list.append(query_openpredict_classifier(curie_to_predict))
    return predictions_list


def query_openpredict_classifier(input_curie, model_id='openpredict-baseline-omim-drugbank'):
    """The main function to query the drug-disease OpenPredict classifier, 
    It queries the previously generated classifier a `.joblib` file 
    in the `data/models` folder
    
    :return: Predictions and scores
    """
    
    parsed_curie = re.search('(.*?):(.*)', input_curie)
    input_namespace = parsed_curie.group(1)
    input_id = parsed_curie.group(2)

    # resources_folder = "data/resources/"
    #features_folder = "data/features/"
    #drugfeatfiles = ['drugs-fingerprint-sim.csv','drugs-se-sim.csv', 
    #                 'drugs-ppi-sim.csv', 'drugs-target-go-sim.csv','drugs-target-seq-sim.csv']
    #diseasefeatfiles =['diseases-hpo-sim.csv',  'diseases-pheno-sim.csv' ]
    #drugfeatfiles = [ os.path.join(features_folder, fn) for fn in drugfeatfiles]
    #diseasefeatfiles = [ os.path.join(features_folder, fn) for fn in diseasefeatfiles]

    ## Get all DFs
    # Merge feature matrix
    #drug_df, disease_df = mergeFeatureMatrix(drugfeatfiles, diseasefeatfiles)
    # (drug_df, disease_df)= load('data/features/drug_disease_dataframes.joblib')

    print("📥 Loading features " + 'features/' + model_id + '.joblib')
    (drug_df, disease_df)= load(get_dir('data/features/' + model_id + '.joblib'))

    # TODO: should we update this file too when we create new runs?
    drugDiseaseKnown = pd.read_csv(get_dir('data/resources/openpredict-omim-drug.csv'),delimiter=',')

    drugDiseaseKnown.rename(columns={'drugid':'Drug','omimid':'Disease'}, inplace=True)
    drugDiseaseKnown.Disease = drugDiseaseKnown.Disease.astype(str)

    # TODO: save json?
    drugDiseaseDict  = set([tuple(x) for x in  drugDiseaseKnown[['Drug','Disease']].values])

    drugwithfeatures = set(drug_df.columns.levels[1].tolist())
    diseaseswithfeatures = set(disease_df.columns.levels[1].tolist())

    # TODO: save json?
    commonDrugs= drugwithfeatures.intersection( drugDiseaseKnown.Drug.unique())
    commonDiseases=  diseaseswithfeatures.intersection(drugDiseaseKnown.Disease.unique() )

    # clf = load('data/models/openpredict-baseline-omim-drugbank.joblib') 
    print('📥 Loading classifier models/' + model_id + '.joblib')
    clf = load(get_dir('data/models/' + model_id + '.joblib'))

    pairs=[]
    classes=[]
    if input_namespace.lower() == "drugbank":
        # Input is a drug, we only iterate on disease
        dr = input_id
        # drug_column_label = "source"
        # disease_column_label = "target"
        for di in commonDiseases:
            cls = (1 if (dr,di) in drugDiseaseDict else 0)
            pairs.append((dr,di))
            classes.append(cls)
    else: 
        # Input is a disease
        di = input_id
        # drug_column_label = "target"
        # disease_column_label = "source"
        for dr in commonDrugs:
            cls = (1 if (dr,di) in drugDiseaseDict else 0)
            pairs.append((dr,di))
            classes.append(cls)

    classes = np.array(classes)
    pairs = np.array(pairs)

    # test_df = createFeaturesSparkOrDF(pairs, classes, drug_df, disease_df)
    test_df = createFeatureDF(pairs, classes, pairs[classes==1], drug_df, disease_df)
    
    # Get list of drug-disease pairs (should be saved somewhere from previous computer?)
    # Another API: given the type, what kind of entities exists?
    # Getting list of Drugs and Diseases:
    # commonDrugs= drugwithfeatures.intersection( drugDiseaseKnown.Drug.unique())
    # commonDiseases=  diseaseswithfeatures.intersection(drugDiseaseKnown.Disease.unique() )
    features = list(test_df.columns.difference(['Drug','Disease','Class']))
    y_proba = clf.predict_proba(test_df[features])

    prediction_df = pd.DataFrame( list(zip(pairs[:,0], pairs[:,1], y_proba[:,1])), columns =['drug','disease','score'])
    prediction_df.sort_values(by='score', inplace=True, ascending=False)
    # prediction_df = pd.DataFrame( list(zip(pairs[:,0], pairs[:,1], y_proba[:,1])), columns =[drug_column_label,disease_column_label,'score'])
    
    # Add namespace to get CURIEs from IDs
    prediction_df["drug"]= "DRUGBANK:" + prediction_df["drug"]
    prediction_df["disease"] ="OMIM:" + prediction_df["disease"]

    # prediction_results=prediction_df.to_json(orient='records')
    prediction_results=prediction_df.to_dict(orient='records')
    return prediction_results

def createFeatureDF(pairs, classes, knownDrugDisease, drugDFs, diseaseDFs):
    """Create the features dataframes.

    :param pairs: Generated pairs
    :param classes: Classes corresponding to the pairs
    :param knownDrugDisease: Known drug-disease associations
    :param drugDFs: Drug dataframes
    :param diseaseDFs: Disease dataframes
    :return: The features dataframe 
    """
    totalNumFeatures = len(drugDFs)*len(diseaseDFs)
    #featureMatri x= np.empty((len(classes),totalNumFeatures), float)
    df =pd.DataFrame(list(zip(pairs[:,0], pairs[:,1], classes)), columns =['Drug','Disease','Class'])
    index = 0
    for i,drug_col in enumerate(drugDFs.columns.levels[0]):
        for j,disease_col in enumerate(diseaseDFs.columns.levels[0]):
            drugDF = drugDFs[drug_col]
            diseaseDF = diseaseDFs[disease_col]
            feature_series = df.apply(lambda row: geometricMean( row.Drug, row.Disease, knownDrugDisease, drugDF, diseaseDF), axis=1)
            #print (feature_series) 
            df["Feature_"+str(drug_col)+'_'+str(disease_col)] = feature_series
    return df

def geometricMean(drug, disease, knownDrugDisease, drugDF, diseaseDF):
    """Compute the geometric means of a drug-disease association using previously generated dataframes

    :param drug: Drug
    :param disease: Disease
    :param knownDrugDisease: Known drug-disease associations
    :param drugDF: Drug dataframe
    :param diseaseDF: Disease dataframe
    """
    a  = drugDF.loc[knownDrugDisease[:,0]][drug].values
    b  = diseaseDF.loc[knownDrugDisease[:,1]][disease].values
    c = np.sqrt( np.multiply(a,b) )
    ix2 = (knownDrugDisease == [drug, disease])
    c[ix2[:,1]& ix2[:,0]]=0.0
    return float(max(c))