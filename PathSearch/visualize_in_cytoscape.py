# This script will create a cytoscape image for a given subgraph to the same directory of the given 
# input-subgraph-file. Cytoscape must be running.

import re
from inputs import *
from visualize_subgraph import create_cytoscape_png, create_noa_file, create_node_attributes
import pandas as pd


#Have Cytoscape running, will only output png of subgraph(s) when subgraph.csv and subgraph_attributions.noa exist
def main():
    parser=argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--input-nodes-file",dest="InputNodesFile",required=True,help="InputNodesFile")

    parser.add_argument("--input-subgraph-file",dest="InputSubgraphFile",required=True,help="InputSubgraphFile")

    #Generate argument parser and define arguments
    args = parser.parse_args()

    input_nodes_file = args.InputNodesFile
    input_subgraph_file = args.InputSubgraphFile

    input_nodes_df = pd.read_csv(input_nodes_file, sep="|")
    subgraph_df = pd.read_csv(input_subgraph_file, sep="|")
    if "Subgraph_" in input_subgraph_file:
        subgraph_name = input_subgraph_file.split("/")[-1].replace(".csv","").replace("Subgraph_","")
        output_dir = re.sub(r"/Subgraph_\d+\.csv", "", input_subgraph_file)
    else:
        subgraph_name = ""
        output_dir = re.sub(r"/Subgraph.csv", "", input_subgraph_file)
    subgraph_attributes_df = create_node_attributes(input_nodes_df,subgraph_df)

    create_noa_file(subgraph_attributes_df,output_dir,override_filename=subgraph_name)

    create_cytoscape_png(subgraph_df,subgraph_attributes_df,output_dir,override_filename=subgraph_name)

if __name__ == '__main__':
    main()