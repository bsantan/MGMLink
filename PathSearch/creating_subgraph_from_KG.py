from inputs import *
from create_graph import create_graph
from assign_nodes import interactive_search_wrapper
from create_subgraph import subgraph_prioritized_path_cs
from create_subgraph import subgraph_prioritized_path_pdp
from create_subgraph import user_defined_edge_exclusion
from create_subgraph import get_neighboring_nodes
from visualize_subgraph import output_visualization
from evaluation import *

def main():

    input_dir,output_dir,kg_type,embedding_dimensions,weights,search_type,pdp_weight,first_order_nodes = generate_arguments()

    triples_list_file,labels_file,input_file = get_graph_files(input_dir,output_dir, kg_type)

    print("Creating knowledge graph object from inputs.....")

    g = create_graph(triples_list_file,labels_file, kg_type)
    
    print("Mapping between user inputs and KG nodes.......")
    
    s = interactive_search_wrapper(g, input_file, output_dir,kg_type)

    print("Mapping complete")
    print(s)

    if weights == True:
        g = user_defined_edge_exclusion(g,kg_type)

    print("Finding subgraph using user input and KG embeddings for Cosine Similarity......")
    
    if first_order_nodes == True:
        s = get_neighboring_nodes(s,g.edgelist,g.labels_all,kg_type)
        print('with first order nodes: ',s)

    subgraph_cs,path_total_cs = subgraph_prioritized_path_cs(s,g.igraph,g.igraph_nodes,g.labels_all,g.edgelist,weights,search_type,triples_list_file,output_dir,input_dir,embedding_dimensions,kg_type)

    print("Outputting CS visualization......")

    cs_noa_df = output_visualization(s,subgraph_cs,output_dir+'/CosineSimilarity')

    print("Finding subgraph using user input for PDP......")

    subgraph_pdp,path_pdp = subgraph_prioritized_path_pdp(s,g.igraph,g.igraph_nodes,g.labels_all,g.edgelist,weights,search_type,pdp_weight,output_dir,kg_type)
    
    print("Outputting PDP visualization......")

    pdp_noa_df = output_visualization(s,subgraph_pdp,output_dir+'/PDP')

if __name__ == '__main__':
    main()
