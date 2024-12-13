from graph_embeddings import Embeddings
from inputs import *
from create_graph import create_graph
from assign_nodes import interactive_search_wrapper
from create_subgraph import get_contextual_microbes, subgraph_prioritized_path_cs
from create_subgraph import user_defined_edge_exclusion
from evaluation import *

def main():

    input_dir,output_dir,kg_type,embedding_dimensions,embedding_method,weights,search_type,first_order_nodes, num_paths_output = generate_arguments()
    input_type = "experimental_data"
    enable_skipping = False

    triples_list_file,labels_file,input_file = get_graph_files(input_dir,output_dir, kg_type)

    print("Creating knowledge graph object from inputs.....")

    g = create_graph(triples_list_file,labels_file, kg_type)
    
    print("Mapping between user inputs and KG nodes.......")

    s = interactive_search_wrapper(g, input_file, output_dir, input_type,kg_type,enable_skipping)

    print("Mapping complete")
    print(s)

    if weights == True:
        g = user_defined_edge_exclusion(g,kg_type)

    print("Finding subgraph using user input and KG embeddings for Cosine Similarity......")
    
    if first_order_nodes == True:
        s = get_contextual_microbes(s,g.edgelist,g.labels_all,kg_type,output_dir,input_type)
        print('with first order nodes: ',s)

    groups = dict(tuple(s.groupby(['source', 'target'])))

    if embedding_method == "both":
        all_embedding_methods = ['node2vec', 'transe']
    else:
        all_embedding_methods = [embedding_method]

    for _, group in groups.items():

        new_source_label = group.iloc[0].loc["source"].replace(" ","_").replace("/","").replace(":","_")
        new_target_label = group.iloc[0].loc["target"].replace(" ","_").replace("/","").replace(":","_")
        pair_subfolder_name = new_source_label + "__" + new_target_label

        for embedding_method in all_embedding_methods:

            # Prepare embeddings
            e = Embeddings(triples_list_file,labels_file,input_dir,embedding_dimensions, kg_type)
            emb,entity_map = e.generate_graph_embeddings(embedding_method)

            pair_output_dir = output_dir + '/' + pair_subfolder_name + '/' + embedding_method
            if os.path.exists(pair_output_dir):
                continue
            print("Finding paths for ", pair_subfolder_name, " using ", embedding_method)

            # Input a dataframe for pair of nodes, need [[pair]]
            subgraph_cs_list,all_paths_cs_values,all_path_nodes = subgraph_prioritized_path_cs(group, g,weights,search_type,triples_list_file,labels_file,pair_output_dir,input_dir,emb,entity_map,embedding_method,kg_type, "Shortest_Path",num_paths_output,group,pair_output_dir)

            print("Finding subgraph using user input for top Metapath......")

            subgraph_cs_list,all_paths_cs_values,all_path_nodes = subgraph_prioritized_path_cs(group, g,weights,search_type,triples_list_file,labels_file,pair_output_dir,input_dir,emb,entity_map,embedding_method,kg_type,"Metapath",num_paths_output,group,pair_output_dir)

            compare_alorithms_similarities("Shortest_Path","Metapath", pair_output_dir)

if __name__ == '__main__':
    main()
