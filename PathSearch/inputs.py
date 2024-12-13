import argparse
import os

#Define arguments for each required and optional input
def define_arguments():
    parser=argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    ## Required inputs
    parser.add_argument("--input-dir",dest="InputDir",required=True,help="InputDir")

    parser.add_argument("--output-dir",dest="OutputDir",required=True,help="OutputDir")

    parser.add_argument("--knowledge-graph",dest="KG",required=True,help="Knowledge Graph: either 'pkl' for PheKnowLator or 'kg-covid19' for KG-Covid19")

    ## Optional inputs
    parser.add_argument("--embedding-dimensions",dest="EmbeddingDimensions",required=False,default=128,help="EmbeddingDimensions")

    parser.add_argument("--embedding-method",dest="EmbeddingMethod",required=False,default="node2vec",help="EmbeddingMethod")

    parser.add_argument("--weights",dest="Weights",required=False,help="Weights", type = bool, default = False)

    parser.add_argument("--search-type",dest="SearchType",required=False,default='all',help="SearchType")

    parser.add_argument("--first-order-nodes",dest="FirstOrderNodes",required=False,default=False,help='FirstOrderNodes',type= bool)

    parser.add_argument("--num-paths-output",dest="NumPathsOutput",required=False,default=20,help='NumPathsOutput',type= int)

    return parser

# Wrapper function
def generate_arguments():

    #Generate argument parser and define arguments
    parser = define_arguments()
    args = parser.parse_args()

    input_dir = args.InputDir
    output_dir = args.OutputDir
    kg_type = args.KG
    embedding_dimensions = args.EmbeddingDimensions
    embedding_method = args.EmbeddingMethod
    weights = args.Weights
    search_type = args.SearchType
    first_order_nodes = args.FirstOrderNodes
    num_paths_output =args.NumPathsOutput

    return input_dir,output_dir,kg_type,embedding_dimensions,embedding_method,weights,search_type,first_order_nodes,num_paths_output

def get_graph_files(input_dir,output_dir, kg_type):

    if kg_type == "pkl" or kg_type == 'mgmlink':
        existence_dict = {
            'PheKnowLator_v3.0.2_full_instance_relationsOnly_OWLNETS_Triples_Identifiers':'false',
            'PheKnowLator_v3.0.2_full_instance_relationsOnly_OWLNETS_NodeLabels':'false',
            '_example_input':'false',
        }

        for k in list(existence_dict.keys()):
            for fname in os.listdir(input_dir):
                if k in fname:
                    if k == 'PheKnowLator_v3.0.2_full_instance_relationsOnly_OWLNETS_Triples_Identifiers':
                        triples_list_file = input_dir + '/' + fname
                    if k == 'PheKnowLator_v3.0.2_full_instance_relationsOnly_OWLNETS_NodeLabels':
                        labels_file = input_dir + '/' + fname
                    if k == '_example_input':
                        input_file = input_dir + '/' + fname
                    existence_dict[k] = 'true'

    if kg_type == "kg-covid19":
        existence_dict = {
            'merged-kg_edges':'false',
            'merged-kg_nodes':'false',
            '_example_input':'false',
        }

        for k in list(existence_dict.keys()):
            for fname in os.listdir(input_dir):
                if k in fname:
                    if k == 'merged-kg_edges':
                        triples_list_file = input_dir + '/' + fname
                    if k == 'merged-kg_nodes':
                        labels_file = input_dir + '/' + fname
                    if k == '_example_input':
                        input_file = input_dir + '/' + fname
                    existence_dict[k] = 'true'

    #Check for existence of all necessary files, error if not

    #### Add exception
    for k in existence_dict:
        if existence_dict[k] == 'false':
            raise Exception('Missing file in input directory: ' + k)

    #Check for existence of output directory
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print(input_file)
    return triples_list_file,labels_file,input_file
