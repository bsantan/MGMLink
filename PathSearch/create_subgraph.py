# Given a starting graph of node pairs, find all paths between them to create a subgraph
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
    if kg_type == 'pkl':
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





    
def subgraph_prioritized_path_cs(input_nodes_df,graph,g_nodes,labels_all,triples_df,weights,search_type,triples_file,output_dir,input_dir,embedding_dimensions,kg_type):

    input_nodes_df.columns= input_nodes_df.columns.str.lower()

    all_paths = []

    num_paths_df = pd.DataFrame(columns = ['source_node','target_node','num_paths'])

    for i in tqdm(range(len(input_nodes_df))):
        df_paths = pd.DataFrame()
        start_node = input_nodes_df.iloc[i].loc['source_label']
        end_node = input_nodes_df.iloc[i].loc['target_label']
        status,path_nodes,cs_shortest_path_df,paths_total_cs = prioritize_path_cs(start_node,end_node,graph,g_nodes,labels_all,triples_df,weights,
        search_type,triples_file,output_dir,input_dir,embedding_dimensions,kg_type)
        if status == False:
            print('No path between: ',start_node,' and ',end_node)
            continue
        all_paths.append(cs_shortest_path_df)
        df_paths['source_node'] = [start_node]
        df_paths['target_node'] = [end_node]
        df_paths['num_paths'] = [len(path_nodes)]
        num_paths_df = pd.concat([num_paths_df,df_paths],axis=0)
        #Output path list to file where index will match the pair# in the _Input_Nodes_.csv
        output_path_lists(output_dir,paths_total_cs,'CosineSimilarity',i)

    df = pd.concat(all_paths)
    df.reset_index(drop=True, inplace=True)
    #Remove duplicate edges
    df = df.drop_duplicates(subset=['S','P','O'])

    output_num_paths_pairs(output_dir,num_paths_df,'CosineSimilarity')

    return df,paths_total_cs

def subgraph_prioritized_path_pdp(input_nodes_df,graph,g_nodes,labels_all,triples_df,weights,search_type,pdp_weight,output_dir, kg_type):

    input_nodes_df.columns= input_nodes_df.columns.str.lower()

    all_paths = []

    num_paths_df = pd.DataFrame(columns = ['source_node','target_node','num_paths'])

    for i in tqdm(range(len(input_nodes_df))):
        df_paths = pd.DataFrame()
        start_node = input_nodes_df.iloc[i].loc['source_label']
        end_node = input_nodes_df.iloc[i].loc['target_label']
        status,path_nodes,pdp_shortest_path_df,paths_pdp = prioritize_path_pdp(start_node,end_node,graph,g_nodes,labels_all,triples_df,weights,search_type,pdp_weight,kg_type)
        if status == False:
            print('No path between: ',start_node,' and ',end_node)
            continue
        all_paths.append(pdp_shortest_path_df)
        df_paths['source_node'] = [start_node]
        df_paths['target_node'] = [end_node]
        df_paths['num_paths'] = [len(path_nodes)]
        num_paths_df = pd.concat([num_paths_df,df_paths],axis=0)
        #Output path list to file where index will match the pair# in the _Input_Nodes_.csv
        output_path_lists(output_dir,paths_pdp,'PDP',i)

    df = pd.concat(all_paths)
    df.reset_index(drop=True, inplace=True)
    #Remove duplicate edges
    df = df.drop_duplicates(subset=['S','P','O'])

    output_num_paths_pairs(output_dir,num_paths_df,'PDP')

    return df,paths_pdp

#Create new input_nodes_df that includes first order nodes as source
def get_neighboring_nodes(input_nodes_df,triples_df,labels_all,kg_type):

    uninteresting_first_order_nodes = [get_uri(labels_all,'Homo sapiens',kg_type),get_uri(labels_all,'Mus musculus',kg_type),get_uri(labels_all,'lower digestive tract',kg_type)]
    uninteresting_relationships = [get_uri(labels_all,'subClassOf',kg_type),get_uri(labels_all,'located in',kg_type)]

    input_nodes_microbes = [i for i in input_nodes_df['source_label'] if 'CONTEXTUAL' in i]
    input_nodes_target = input_nodes_df.iloc[0].loc['target_label']

    #New input_nodes_df to include first order nodes
    #Use this to include shortest path search between microbe and target
    #input_nodes_neighbors_df = copy.deepcopy(input_nodes_df)

    input_nodes_neighbors_list = []

    #For each microbe, get all first order nodes
    for microbe in input_nodes_microbes:
        microbe_uri = get_uri(labels_all,microbe,kg_type)
        #Identify where microbe is the source node in a triple, will be uris in df
        df = triples_df.loc[(triples_df['subject'] == microbe_uri) & (~triples_df['predicate'].isin(uninteresting_relationships)) & (~triples_df['object'].isin(uninteresting_first_order_nodes))]

        #Go through every target for the corresponding shortest path from this first order node to microbes
        
        for i in range(len(df)):
            s = get_label(labels_all,df.iloc[i].loc['object'],kg_type)
            new_pair = [s,input_nodes_target,s,input_nodes_target]
            #input_nodes_neighbors_df = input_nodes_neighbors_df.append(new_pair_df,ignore_index=True)
            microbe_pair = [microbe,s,microbe,s]
            input_nodes_neighbors_list.append(new_pair)
            input_nodes_neighbors_list.append(microbe_pair)
            #input_nodes_neighbors_df = input_nodes_neighbors_df.append(microbe_pair_df,ignore_index=True)

    #Use this to only include the first neighbor node
    input_nodes_neighbors_df = pd.DataFrame(input_nodes_neighbors_list,columns = ['source','target','source_label','target_label'])

    return input_nodes_neighbors_df