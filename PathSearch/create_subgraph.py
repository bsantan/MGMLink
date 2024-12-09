# Given a starting graph of node pairs, find all paths between them to create a subgraph
import os
import sys
from assign_nodes import check_input_existence, create_input_file
from visualize_subgraph import output_visualization
from find_path import *
import pandas as pd
from tqdm import tqdm
from evaluation import output_path_lists
from evaluation import output_num_paths_pairs
import copy

def subgraph_shortest_path(input_nodes_df,graph,g_nodes,labels_all,triples_df,weights,search_type):

    input_nodes_df.columns= input_nodes_df.columns.str.lower()

    all_paths = []

    for i in range(len(input_nodes_df)):
        start_node = input_nodes_df.iloc[i].loc['source_label']
        end_node = input_nodes_df.iloc[i].loc['target_label']
        shortest_path_df = find_shortest_path(start_node,end_node,graph,g_nodes,labels_all,triples_df,weights,search_type)
        all_paths.append(shortest_path_df)

    df = pd.concat(all_paths)
    df.reset_index(drop=True, inplace=True)
    #Remove duplicate edges
    df = df.drop_duplicates(subset=['S','P','O'])

    return df

# Have user define weights to upweight
def user_defined_edge_weights(graph, triples_df,kg_type ):
    if kg_type == 'pkl' or kg_type == "mgmlink":
        edges = graph.labels_all[graph.labels_all['entity_type'] == 'RELATIONS'].label.tolist()
        print("### Unique Edges in Knowledge Graph ###")
        print('\n'.join(edges))
        still_adding = True
        to_weight= []
        print('\n')
        print('Input the edges to avoid in the path search (if possible). When finished input "Done."')
        while(still_adding):
            user_input = input('Edge or "Done": ')
            if user_input == 'Done':
                still_adding = False
            else:
                to_weight.append(user_input)
        to_weight = graph.labels_all[graph.labels_all['label'].isin(to_weight)]['entity_uri'].tolist()

    if kg_type == 'kg-covid19':
        edges = set(list(graph.igraph.es['predicate']))
        print("### Unique Edges in Knowledge Graph ###")
        print('\n'.join(edges))
        still_adding = True
        to_weight= []
        print('\n')
        print('Input the edges to avoid in the path search (if possible). When finished input "Done"')
        while(still_adding):
            user_input = input('Edge or "Done"')
            if user_input == 'Done':
                still_adding = False
            else:
                to_weight.append(user_input)

    edges= graph.igraph.es['predicate']
    graph.igraph.es['weight'] = [10 if x in to_weight else 1 for x in edges]
    return(graph)

# Have user define weights to upweight
def user_defined_edge_exclusion(graph,kg_type ):
    if kg_type == 'pkl':
        edges = graph.labels_all[graph.labels_all['entity_type'] == 'RELATIONS'].label.tolist()
        print("### Unique Edges in Knowledge Graph ###")
        print('\n'.join(edges))
        still_adding = True
        to_drop= []
        print('\n')
        print('Input the edges to avoid in the path search (if possible). When finished input "Done."')
        while(still_adding):
            user_input = input('Edge or "Done": ')
            if user_input == 'Done':
                still_adding = False
            else:
                to_drop.append(user_input)
        to_drop = graph.labels_all[graph.labels_all['label'].isin(to_drop)]['entity_uri'].tolist()
        
    if kg_type == 'kg-covid19':
        edges = set(list(graph.igraph.es['predicate']))
        print("### Unique Edges in Knowledge Graph ###")
        print('\n'.join(edges))
        still_adding = True
        to_drop= []
        print('\n')
        print('Input the edges to avoid in the path search (if possible). When finished input "Done"')
        while(still_adding):
            user_input = input('Edge or "Done"')
            if user_input == 'Done':
                still_adding = False
            else:
                to_drop.append(user_input)
    for edge in to_drop:
        graph.igraph.delete_edges(graph.igraph.es.select(predicate = edge))
    return(graph)

# Edges to remove
def automatic_defined_edge_exclusion(graph,kg_type):

    print("original edgelist length: ",len(graph.edgelist))
    uninteresting_relationships = [get_uri(graph.labels_all,'subClassOf',kg_type),get_uri(graph.labels_all,'located in',kg_type)]

    if kg_type == 'mgmlink':
        to_drop = uninteresting_relationships
    for edge in to_drop:
        # Remove from graph object
        graph.igraph.delete_edges(graph.igraph.es.select(predicate = edge))
        # Remove from df
        graph.edgelist = graph.edgelist[graph.edgelist["predicate"] != edge]

    print("new edgelist length: ",len(graph.edgelist))
    return graph

# Nodes to remove
def automatic_defined_node_exclusion(graph,kg_type):
    
    uninteresting_first_order_nodes = [get_uri(graph.labels_all,'Homo sapiens',kg_type),get_uri(graph.labels_all,'Mus musculus',kg_type),get_uri(graph.labels_all,'lower digestive tract',kg_type)]
    
    if kg_type == 'mgmlink':
        print("original edgelist length: ",len(graph.edgelist))
        print("original nodes length: ",len(graph.labels_all))
        to_drop = uninteresting_first_order_nodes
    print("Removing nodes from KG")
    # Remove from graph object
    for uri in tqdm(to_drop):
        # Get the indices of vertices with corresponding label
        indices_to_delete = [v.index for v in graph.igraph.vs if v["name"] == uri]
        # Remove the vertices by their indices
        try:
            graph.igraph.delete_vertices(indices_to_delete)
        except KeyError:
            print('Specified node to be removed does not exist. Update PHEKNOWLATOR_BROAD_NODES_DICT in constants.py.')
            sys.exit(1)
    # Remove from dfs
    graph.labels_all = graph.labels_all[~graph.labels_all["entity_uri"].isin(to_drop)]
    graph.edgelist = graph.edgelist[~(graph.edgelist["subject"].isin(to_drop) | graph.edgelist["object"].isin(to_drop))]
    print("new edgelist length: ",len(graph.edgelist))
    print("new nodes length: ",len(graph.labels_all))
    return graph

def subgraph_prioritized_path_cs(input_nodes_df,graph,weights,search_type,triples_file,output_dir,input_dir,embedding_dimensions,kg_type, search_algorithm,num_paths_output,group, pair_output_dir):

    input_nodes_df.columns= input_nodes_df.columns.str.lower()
    if search_type == "both":
        all_search_types = ["all", "out"]
    else:
        all_search_types = [search_type]

    all_paths = []

    num_paths_df = pd.DataFrame(columns = ['source_node','target_node','num_paths'])

    #Dict of all shortest paths for subgraph
    all_path_nodes = {}

    id_keys_df = pd.DataFrame(columns = ["Original","New"])

    for i in tqdm(range(len(input_nodes_df))):
        inputpath_index = str(i)
        df_paths = pd.DataFrame()
        start_node = input_nodes_df.iloc[i].loc['source_label']
        end_node = input_nodes_df.iloc[i].loc['target_label']
        node_pair = input_nodes_df.iloc[i]
        for search_type in all_search_types:
            path_nodes,id_keys_df,metapaths_key = get_paths(node_pair,graph,weights,search_type,triples_file,input_dir, output_dir, kg_type, search_algorithm, id_keys_df)
            # Convert all path_nodes to labels
            if search_algorithm == "Shortest_Path":
                df_paths['search_type'] = [search_type]
                df_paths['source_node'] = [start_node]
                df_paths['target_node'] = [end_node]
                df_paths['num_paths'] = [len(path_nodes)]
                num_paths_df = pd.concat([num_paths_df,df_paths],axis=0)
                # Prioritize using cosine sim
                cs_shortest_path_df,all_paths_cs_values,chosen_path_nodes_cs,id_keys_df = prioritize_path_cs(path_nodes,input_nodes_df,graph,weights,search_type,triples_file,input_dir,embedding_dimensions,kg_type,search_algorithm,id_keys_df)
                all_paths.append(cs_shortest_path_df)
                #Output path list to file where index will match the pair# in the _Input_Nodes_.csv
                #Get sum of all cosine values in value_list
                path_list = list(map(sum, all_paths_cs_values))
                for outputpath_idx,p in enumerate(path_nodes[0:num_paths_output]):
                    df = pd.DataFrame()
                    df = define_path_triples(graph,[p],search_type)
                    df = convert_to_labels(df,graph.labels_all,kg_type,input_nodes_df)
                    outputpath_index = str(outputpath_idx)
                    cs_noa_df = output_visualization(input_nodes_df,df,output_dir + '/' + search_algorithm + '_' + search_type + "/All_Paths_" + inputpath_index + "/",outputpath_index)
                output_path_lists(output_dir,path_list,'CosineSimilarity_'+search_algorithm+'_'+search_type,i,path_nodes)
                # Output chosen cosine sim
                cs_noa_df = output_visualization(group, cs_shortest_path_df,pair_output_dir+'/CosineSimilarity_Shortest_Path_' + search_type + '_' + inputpath_index)
            elif search_algorithm == "Metapath":
                # if len(path_nodes[0]) != 0:
                # Length of metapath_keys will match length of path_nodes
                for metapath_idx,metapath_val in metapaths_key.items():
                    metapath_index = str(metapath_idx)
                    metapath_path_nodes = path_nodes[metapath_idx]
                    df_paths['metapath'] = [metapaths_key[metapath_idx]]
                    df_paths['source_node'] = [start_node]
                    df_paths['target_node'] = [end_node]
                    df_paths['num_paths'] = [len(metapath_path_nodes)]
                    num_paths_df = pd.concat([num_paths_df,df_paths],axis=0)
                    # Path nodes from metapath search already have predicate
                    # paths_dfs_dict is in same order as metapaths_key
                    # Prioritize using cosine sim
                    cs_shortest_path_df,all_paths_cs_values,chosen_path_nodes_cs,id_keys_df = prioritize_path_cs(metapath_path_nodes,input_nodes_df,graph,weights,search_type,triples_file,input_dir,embedding_dimensions,kg_type,search_algorithm,id_keys_df)
                    all_paths.append(cs_shortest_path_df)
                    #Output path list to file where index will match the pair# in the _Input_Nodes_.csv
                    #Get sum of all cosine values in value_list
                    path_list = list(map(sum, all_paths_cs_values))
                    paths_dfs_dict = define_metapath_triples(metapath_path_nodes[0:num_paths_output])
                    for outputpath_idx,path_val in paths_dfs_dict.items():
                        outputpath_index = str(outputpath_idx)
                        df = convert_to_labels(path_val,graph.labels_all,kg_type,input_nodes_df)
                        if len(df) > 0:
                            cs_noa_df = output_visualization(input_nodes_df,df,output_dir + '/' + search_algorithm + "_Path" + metapath_index + "/All_Paths_" + inputpath_index + "/",outputpath_index)
                        else:
                            continue
                    output_path_lists(output_dir,path_list,'CosineSimilarity_'+search_algorithm+'_Path'+metapath_index,i,metapath_path_nodes)
                    # Output chosen cosine sim
                    cs_noa_df = output_visualization(group, cs_shortest_path_df,pair_output_dir+'/CosineSimilarity_Metapath_Path' + metapath_index + "_" + inputpath_index)

    # Output number of paths for each pair given as single file
    output_num_paths_pairs(output_dir,num_paths_df,search_algorithm)

    return all_paths,all_paths_cs_values,all_path_nodes #df

#Create new input_nodes_df that includes first order nodes as source
def get_contextual_microbes(input_nodes_df,triples_df,labels_all,kg_type,output_dir,input_type):

    #Check for existence based on input type
    exists = check_input_existence(output_dir,input_type + "_contextual")
    # exists = ["true","/Users/brooksantangelo/Documents/Repositories/MGMLink/Output/_experimental_data_Input_Nodes_.csv"]
    if(exists[0] == 'false'):
        input_nodes_neighbors_df = pd.DataFrame()
        for i in range(len(input_nodes_df)):
            if 'NCBITaxon_' in input_nodes_df.iloc[i].loc['source_id']: 
                original_microbe_id = input_nodes_df.iloc[i].loc['source_id']
                new_microbial_uris = triples_df.loc[(triples_df['object'] == original_microbe_id) & (triples_df['predicate'] == "http://www.w3.org/2000/01/rdf-schema#subClassOf") & (triples_df['subject'].str.contains("pkt")),"subject"].tolist()
                if len(new_microbial_uris) > 0:
                    # Get Labels 
                    new_microbial_labels = []
                    for uri in new_microbial_uris:
                        l = get_label(labels_all,uri,kg_type)
                        new_microbial_labels.append(l)
                else:
                    new_microbial_uris = [input_nodes_df.iloc[i].loc['source_id']]
                    new_microbial_labels = [input_nodes_df.iloc[i].loc['source_label']]
            else:
                new_microbial_uris = [input_nodes_df.iloc[i].loc['source_id']]
                new_microbial_labels = [input_nodes_df.iloc[i].loc['source_label']]
            input_nodes_source_label = input_nodes_df.iloc[i].loc['source_label']
            input_nodes_target_id = input_nodes_df.iloc[i].loc['target_id']
            input_nodes_target_label = input_nodes_df.iloc[i].loc['target_label']
            all_source_labels = [input_nodes_source_label] * len(new_microbial_uris)
            all_target_ids = [input_nodes_target_id] * len(new_microbial_uris)
            all_target_labels = [input_nodes_target_label] * len(new_microbial_uris)
            rows = []
            for r in range(len(new_microbial_uris)):
                rows.append([all_source_labels[r], all_target_labels[r], new_microbial_labels[r], all_target_labels[r], new_microbial_uris[r], all_target_ids[r]])
            df = pd.DataFrame(rows,columns = ['source','target','source_label','target_label','source_id','target_id'])
            input_nodes_neighbors_df = pd.concat([df, input_nodes_neighbors_df],axis=0)

        create_input_file(input_nodes_neighbors_df,output_dir,input_type + "_contextual")

    else:
        print('Node mapping file exists... moving to embedding creation')
        mapped_file = output_dir + '/'+ exists[1]
        input_nodes_neighbors_df = pd.read_csv(mapped_file, sep = "|")

    return input_nodes_neighbors_df

def subgraph_all_paths(input_nodes_df,graph,weights,search_type,triples_file,output_dir,input_dir,embedding_dimensions,kg_type, search_algorithm, find_graph_similarity = False,existing_path_nodes = 'none'):

    input_nodes_df.columns= input_nodes_df.columns.str.lower()

    num_paths_df = pd.DataFrame(columns = ['source_node','target_node','num_paths'])

    #List of all chosen paths for subgraph
    #all_chosen_path_nodes = []

    #Dict of all shortest paths for subgraph
    all_path_nodes = {}

    id_keys_df = pd.DataFrame(columns = ["Original","New"])

    if search_algorithm == "Metapath_Neighbors":
        # Transform input_nodes into relevant metapath objects and append to original input_nodes_df
        input_nodes_df,id_keys_df = expand_neighbors(input_nodes_df,input_dir,triples_file,id_keys_df,graph.labels_all,kg_type)
        print("og input_nodes_df")
        print(input_nodes_df)
        input_nodes_df = input_nodes_df[~input_nodes_df["target_id"].str.contains("http:")]
        print("new input_nodes_df")
        print(input_nodes_df)

    for i in tqdm(range(len(input_nodes_df))):
        df_paths = pd.DataFrame()
        start_node = input_nodes_df.iloc[i].loc['source_label']
        end_node = input_nodes_df.iloc[i].loc['target_label']
        start_node_uri = input_nodes_df.iloc[i].loc['source_id']
        if existing_path_nodes != 'none':
            pair_path_nodes = existing_path_nodes[start_node + end_node]
        else:
            pair_path_nodes = 'none'
        node_pair = input_nodes_df.iloc[i]
        path_nodes, id_keys_df = path_search_no_prioritization(node_pair, graph, triples_file,input_dir, kg_type, search_algorithm, id_keys_df)
        df_paths['source_node'] = [start_node]
        df_paths['target_node'] = [end_node]
        df_paths['num_paths'] = [len(path_nodes)]
        num_paths_df = pd.concat([num_paths_df,df_paths],axis=0)
        # Path nodes from metapath search already have predicate
        paths_dfs_dict = define_metapath_triples(path_nodes)

        paths_dfs_list = []
        for _,v in paths_dfs_dict.items():
            df = convert_to_labels(v,graph.labels_all,kg_type,input_nodes_df)
            paths_dfs_list.append(df)
        # Keep track of every path found by uri so that you can search them later
        all_path_nodes[start_node + end_node] = path_nodes

    # Write to file if data exists
    print("id_keys_df: ",id_keys_df)
    if len(id_keys_df) > 0:
        if not os.path.exists(output_dir + '/' + search_algorithm): os.mkdir(output_dir + '/' + search_algorithm)
        id_keys_df.to_csv(output_dir + '/' + search_algorithm + "/id_keys_df.csv",sep='|',index=False)

    output_num_paths_pairs(output_dir,num_paths_df,search_algorithm)

    return paths_dfs_list, all_path_nodes
