from graph import KnowledgeGraph
import pandas as pd
import csv
import json
from igraph import * 


###Read in all files, outputs triples and labels as a df
def process_pkl_files(triples_file,labels_file):
    
    triples_df = pd.read_csv(triples_file,sep = '	', quoting=csv.QUOTE_NONE)
    triples_df.columns.str.lower()

    triples_df.replace({'<': ''}, regex=True, inplace=True)
    triples_df.replace({'>': ''}, regex=True, inplace=True)

    labels = pd.read_csv(labels_file, sep = '	', quoting=csv.QUOTE_NONE)
    labels.columns.str.lower()

    #Remove brackets from URI
    labels['entity_uri'] = labels['entity_uri'].str.replace("<","")
    labels['entity_uri'] = labels['entity_uri'].str.replace(">","")


    return triples_df,labels

#Creates igraph object and a list of nodes
def create_igraph_graph(edgelist_df,labels):

    edgelist_df = edgelist_df[['subject', 'object', 'predicate']]

    g = Graph.DataFrame(edgelist_df,directed=True,use_vids=False)

    g_nodes = g.vs()['name']

    return g,g_nodes 

# Wrapper function
# Includes a "kg_type" parameter for graph type. Options include 'pkl' for PheKnowLator and 'kg-covid19' for KG-Covid19
def create_graph(triples_file,labels_file, kg_type = "pkl"):
    if kg_type == "pkl":
        triples_df,labels = process_pkl_files(triples_file,labels_file)
    elif kg_type == "kg-covid19":
        triples_df,labels = process_kg_covid19_files(triples_file,labels_file)
    elif kg_type == "mgmlink":
        triples_df,labels = process_mgmlink_files(triples_file,labels_file)
        triples_df = triples_df.drop_duplicates()
    else:
        raise Exception('Invalid graph type! Please set kg_type to "pkl", "kg-covid19", or "mgmlink')

    g_igraph,g_nodes_igraph = create_igraph_graph(triples_df,labels)
    # Created a PKL class instance
    pkl_graph = KnowledgeGraph(triples_df,labels,g_igraph,g_nodes_igraph)

    return pkl_graph





###Read in all kg_covid19 files, outputs triples and labels as a df
def process_kg_covid19_files(triples_file,labels_file):
    triples_df = pd.read_csv(triples_file,sep = '\t', usecols = ['subject', 'object', 'predicate'])
    triples_df.columns.str.lower()

    labels = pd.read_csv(labels_file, sep = '\t', usecols = ['id','name','description','xrefs','synonym'])
    labels.columns = ['id','label', 'description/definition','synonym','entity_uri']
    labels.loc[pd.isna(labels["label"]),'label'] = labels.loc[pd.isna(labels["label"]),'id']
    labels.loc[pd.isna(labels["entity_uri"]),'entity_uri'] = labels.loc[pd.isna(labels["entity_uri"]),'id']

    
    return triples_df,labels


###Read in all files, outputs triples and labels as a df
def process_mgmlink_files(triples_file,labels_file):
    
    triples_df = pd.read_csv(triples_file,sep = '	', quoting=csv.QUOTE_NONE)
    triples_df.columns.str.lower()

    triples_df.replace({'<': ''}, regex=True, inplace=True)
    triples_df.replace({'>': ''}, regex=True, inplace=True)

    triples_df.rename(columns = {'Subject':'subject','Predicate':'predicate','Object':'object'},inplace=True)

    labels = pd.read_csv(labels_file, sep = '	', quoting=csv.QUOTE_NONE)
    labels.columns.str.lower()

    labels.rename(columns = {'Identifier':'entity_uri','Label':'label'},inplace=True)

    #Remove brackets from URI
    labels['entity_uri'] = labels['entity_uri'].str.replace("<","")
    labels['entity_uri'] = labels['entity_uri'].str.replace(">","")

    return triples_df,labels