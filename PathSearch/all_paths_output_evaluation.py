# This script will create a table with the path metadata for all data generated in the given output-dir. 
# The output file is All_Paths_Results.csv.

import argparse
import os
import pandas as pd


def main():

    parser=argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--output-dir",dest="OutputDir",required=True,help="OutputDir")
    parser.add_argument("--input-nodes-file",dest="InputNodesFile",required=True,help="InputNodesFile")

    #Generate argument parser and define arguments
    args = parser.parse_args()

    output_dir = args.OutputDir
    input_nodes_file = args.InputNodesFile

    input_nodes_df = pd.read_csv(input_nodes_file, sep="|")

    groups = dict(tuple(input_nodes_df.groupby(['source', 'target'])))


    shorest_path_params_replacements = {'all': 'undirected', 'out': 'directed'}

    path_results_df = pd.DataFrame()

    for _, group in groups.items():

        new_source_label = group.iloc[0].loc["source"].replace(" ","_").replace("/","").replace(":","_")
        new_target_label = group.iloc[0].loc["target"].replace(" ","_").replace("/","").replace(":","_")
        pair_subfolder_name = new_source_label + "__" + new_target_label

        # Only need results from one embedding method
        eval_output_dir = output_dir + '/' + pair_subfolder_name + '/node2vec/Evaluation_Files'

        num_paths_substring = "num_paths_"
        shortest_path_files = [f for f in os.listdir(eval_output_dir) if num_paths_substring + "Shortest_Path" in f]
        metapath_files = [f for f in os.listdir(eval_output_dir) if num_paths_substring + "Metapath" in f]

        for l in [shortest_path_files,metapath_files]:
            for f in l:
                new_df = pd.DataFrame()
                df = pd.read_csv(eval_output_dir + "/" + f,sep=',')
                # source_node = df.iloc[0].loc["source_node"].replace("CONTEXTUAL ","")
                target_node = df.iloc[0].loc["target_node"]
                all_pairs = [(df.iloc[i].loc["source_node"].replace("CONTEXTUAL ","") + ", " + target_node) for i in range(len(df))]
                # all_pairs = [pair for i in range(len(df))]
                if "Shortest_Path" in f:
                    method = ["all shortest paths" for i in range(len(df))]
                    params = df["search_type"].tolist()
                    new_params = [shorest_path_params_replacements.get(item, item) for item in params]
                elif "Metapath" in f:
                    method = ["template-based" for i in range(len(df))]
                    params = df["metapath"].tolist()
                    new_params = [i.replace("_all_",", ") for i in params]
                # Replace parameter names
                length = [int(x) for x in df["path_length"].tolist()]
                num_paths = df["num_paths"].tolist()
                new_df["Microbe: Disease Pair"] = all_pairs
                new_df["Method"] = method
                new_df["Parameters"] = new_params
                new_df["Path Length"] = length
                new_df["Total Paths"] = num_paths

                path_results_df = pd.concat([path_results_df,new_df],ignore_index=True)

    print("Output: ",output_dir + '/All_Paths_Results.csv')
    path_results_df.to_csv(output_dir + '/All_Paths_Results.csv',sep="\t",index=False)


if __name__ == '__main__':
    main()