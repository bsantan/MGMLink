# This script will perform a ranked comparison of all paths output for a given pair of nodes. 
# The script assumes that the Shortest_Path and the Metapath search methods were each used, 
# and that the comparison is between node2vec and transe emeddings. The output files are 
# Shortest_Path_rank_correlation_embeddings.csv and Metapath_rank_correlation_embeddings.csv, 
# as well as the statistics in Shorest_Path_rank_correlation_embeddings_statistics.txt and 
# Metapath_rank_correlation_embeddings_statistics.csv.  

import argparse
import ast
import csv
import os
import pandas as pd
from scipy.stats import spearmanr

from create_graph import create_graph
from find_path import process_path_nodes_value
from inputs import get_graph_files

def get_cosine_values(input_dir, folder, embedding_method, graph):

    output_folder = input_dir + '/' + folder + '/Evaluation_files'

    cosine_vals_subgraph_1_substring = "paths_list_CosineSimilarity_Shortest_Path_"
    cosine_vals_subgraph_1 = {}
    matching_files_1 = [f for f in os.listdir(output_folder) if cosine_vals_subgraph_1_substring in f]
    # Combine all matching files into a single DataFrame
    print("working through: ",embedding_method)
    for file in matching_files_1:
        file_path = os.path.join(output_folder, file)
        df = pd.read_csv(file_path, delimiter="|")
        entity_list = [i for i in df.columns if "Entity_" in i]
        df['Combined_Entities'] = df[entity_list].apply(
                lambda row: '-'.join(map(str, row)), axis=1
            )
        df[embedding_method + '_Value'] = df['Value'] # .rank(ascending=True) # Rank1
        for i in range(len(df)):
            combined_entities = df.iloc[i].loc['Combined_Entities']
            # rank = df.iloc[i].loc['Rank1']
            embedding_method_value = df.iloc[i].loc[embedding_method + '_Value']
            cosine_vals_subgraph_1[combined_entities] = embedding_method_value

    cosine_vals_subgraph_2_substring = "paths_list_CosineSimilarity_Metapath_"
    cosine_vals_subgraph_2 = {}
    matching_files_2 = [f for f in os.listdir(output_folder) if cosine_vals_subgraph_2_substring in f]
    # Combine all matching files into a single DataFrame
    for file in matching_files_2:
        file_path = os.path.join(output_folder, file)
        df = pd.read_csv(file_path, delimiter="|")
        entity_list = [i for i in df.columns if "Entity_" in i]
        df['Combined_Entities'] = df[entity_list].apply(
            lambda row: '-'.join(map(str, row)), axis=1
        )
        df[embedding_method + '_Value'] = df['Value'] # .rank(ascending=True) # Rank2
        for i in range(len(df)):
            combined_entities = df.iloc[i].loc['Combined_Entities']
            # rank = df.iloc[i].loc['Rank2']
            embedding_method_value = df.iloc[i].loc[embedding_method + '_Value']
            cosine_vals_subgraph_2[combined_entities] = embedding_method_value

    # Convert cosine values to rank
    cosine_vals_subgraph_1_ranks = pd.Series(cosine_vals_subgraph_1).rank(method="max", ascending=False).to_dict()
    cosine_vals_subgraph_2_ranks = pd.Series(cosine_vals_subgraph_2).rank(method="max", ascending=False).to_dict()
    return cosine_vals_subgraph_1_ranks, cosine_vals_subgraph_2_ranks 

def main():
    parser=argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--output-dir",dest="OutputDir",required=True,help="OutputDir")
    parser.add_argument("--input-dir",dest="InputDir",required=True,help="InputDir")

    #Generate argument parser and define arguments
    args = parser.parse_args()

    output_dir = args.OutputDir
    input_dir = args.InputDir

    embedding_methods = ['node2vec', 'transe']
    kg_type = "mgmlink"

    triples_list_file,labels_file,input_file = get_graph_files(input_dir,output_dir, kg_type)
    g = create_graph(triples_list_file,labels_file, kg_type)

    method1_all_vals = []
    method2_all_vals = []
    for emb_method in embedding_methods:
        for f in os.listdir(output_dir):
            if f == emb_method:
                # Returns 2 dictionaries
                method1_vals, method2_vals = get_cosine_values(output_dir,f,emb_method, g)
                method1_all_vals.append(method1_vals)
                method2_all_vals.append(method2_vals)

    # Compute Spearman's rank correlation
    for idx,l in enumerate([method1_all_vals,method2_all_vals]):
        method = "Shorest_Path" if idx == 0 else "Metapath"
        common_keys = sorted(set(l[0].keys()) & set(l[1].keys()))
        # Align values for the same keys
        values1 = [l[0][key] for key in common_keys]
        values2 = [l[1][key] for key in common_keys]
        # Compute Spearman's rank correlation
        correlation, p_value = spearmanr(values1, values2)

        # Save the results to a text file
        with open(output_dir + "/" + method + "_rank_correlation_embeddings_statistics.txt", "w") as f:
            
            f.write(f"Spearman's Rank Correlation: {correlation:.2f}\n")
            f.write(f"p-value: {p_value:.4e}\n")

    # Open a CSV file to write
    with open(output_dir + '/Shortest_Path_rank_correlation_embeddings.csv', mode='w', newline='') as file:
        writer = csv.writer(file)
        
        # Write header row
        writer.writerow(['Path', 'Node2Vec_Rank', 'TransE_Rank'])
        
        # Write rows by iterating through keys (same keys in both dicts)
        for idx,key in enumerate(method1_all_vals[0].keys()):
            writer.writerow(["Path_" + str(idx), int(method1_all_vals[0][key]), int(method1_all_vals[1][key])])

    # Open a CSV file to write
    with open(output_dir + '/Metapath_rank_correlation_embeddings.csv', mode='w', newline='') as file:
        writer = csv.writer(file)
        
        # Write header row
        writer.writerow(['Path', 'Node2Vec_Rank', 'TransE_Rank'])
        
        # Write rows by iterating through keys (same keys in both dicts)
        for idx,key in enumerate(method2_all_vals[0].keys()):
            writer.writerow(["Path_" + str(idx), int(method2_all_vals[0][key]), int(method2_all_vals[1][key])])

if __name__ == '__main__':
    main()