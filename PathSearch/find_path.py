from operator import itemgetter
import os
import re
from constants import METAPATH_SEARCH_MAPS
from duckdb_utils import create_filtered_subject_object_pair_table, create_subject_object_pair_table, drop_table, duckdb_load_table, get_table_count, join_tables_subject_object
from graph_embeddings import Embeddings
import numpy as np
import pandas as pd
from scipy import spatial
from scipy.spatial import distance
from collections import defaultdict
from assign_nodes import unique_nodes
import duckdb


#Go from label to entity_uri (for PKL original labels file) or Label to Idenifier (for microbiome PKL)
# kg_type adds functionality for kg-covid19
def get_uri(labels,value, kg_type):

    if kg_type == 'pkl' or kg_type == "mgmlink":
        uri = labels.loc[labels['label'] == value,'entity_uri'].values[0]
    if kg_type == 'kg-covid19':
        uri = labels.loc[labels['label'] == value,'id'].values[0]
    
        
    return uri

def get_label(labels,value,kg_type):
    if kg_type == 'pkl' or kg_type == 'mgmlink':
        label = labels.loc[labels['entity_uri'] == value,'label'].values[0]
    if kg_type == 'kg-covid19':
        label = labels.loc[labels['id'] == value,'label'].values[0]        
    return label



def get_key(dictionary,value):

    for key, val in dictionary.items():
        if val == value:
            return key

def define_path_triples(graph,path_nodes,search_type):

    #Dict to store all dataframes of shortest mechanisms for this node pair
    mechanism_dfs = {}

    #Keep track of # of mechanisms generated for this node pair in file name for all shortest paths
    count = 1 
    #When there is no connection in graph, path_nodes will equal 1 ([[]]) or when there's a self loop
    if len(path_nodes[0]) != 0:
        for p in range(len(path_nodes)):
            #Dataframe to append each triple to
            full_df = pd.DataFrame()
            # path_nodes contains integers for igraph, uris for networkx
            # n1 = graph.igraph_nodes[path_nodes[p][0]]
            n1 = process_path_nodes_value(graph,path_nodes[p][0],"Shortest_Path")
            for i in range(1,len(path_nodes[p])):
                # n2 = graph.igraph_nodes[path_nodes[p][i]]
                n2 = process_path_nodes_value(graph,path_nodes[p][i],"Shortest_Path")
                if search_type.lower() == 'all':
                    #Try first direction which is n1 --> n2
                    df = graph.edgelist.loc[(graph.edgelist['subject'] == n1) & (graph.edgelist['object'] == n2)]
                    full_df = pd.concat([full_df,df])
                    if len(df) == 0:
                        #If no results, try second direction which is n2 --> n1
                        df = graph.edgelist.loc[(graph.edgelist['object'] == n1) & (graph.edgelist['subject'] == n2)]
                        full_df = pd.concat([full_df,df])
                elif search_type.lower() == 'out':
                    #Only try direction n1 --> n2
                    df = graph.edgelist.loc[(graph.edgelist['subject'] == n1) & (graph.edgelist['object'] == n2)]
                    full_df = pd.concat([full_df,df])
                full_df = full_df.reset_index(drop=True)
                n1 = n2
                                        
            #For all shortest path search
            if len(path_nodes) > 1:
                #Generate df
                full_df.columns = ['S_ID','P_ID','O_ID']
                mechanism_dfs['mech#_'+str(count)] = full_df
                count += 1
                
            #For shortest path search
        if len(path_nodes) == 1:
            #Generate df
            full_df.columns = ['S_ID','P_ID','O_ID']
            return full_df

    # Return empty df if no path found
    else:
        df = pd.DataFrame()
        return df

    #Return dictionary if all shortest paths search
    if len(path_nodes) > 1:
        return mechanism_dfs

def define_metapath_triples(path_nodes):

    triples_df_dict = {}
    for idx, path in enumerate(path_nodes):
        # Covert path of combined triples into triples of S, P, O expecting only IDs
        triples = []
        for i in range(0, len(path) - 2, 2):  # Step by 2 to create overlapping triples
            triples.append(path[i:i + 3])

        # Create a DataFrame with headers S_ID, P_ID, and O_ID
        triples_df = pd.DataFrame(triples, columns=["S_ID", "P_ID", "O_ID"])
        triples_df_dict[idx] = triples_df

    return triples_df_dict

def find_all_shortest_paths(node_pair,graph,weights,search_type, kg_type):

    w = None
    node1, node2 = convert_to_node_uris(node_pair,graph,kg_type)
    #Add weights if specified
    if weights:
        w = graph.es["weight"]
    else:
        w = None

    #Dict to store all dataframes of shortest mechanisms for this node pair
    mechanism_dfs = {}

    #list of nodes
    path_nodes = graph.igraph.get_all_shortest_paths(v=node1, to=node2, weights=w, mode=search_type)
    
    #Remove duplicates for bidirectional nodes, only matters when search type=all for mode
    path_nodes = list(set(tuple(x) for x in path_nodes))
    path_nodes = [list(tup) for tup in path_nodes]
    path_nodes = sorted(path_nodes,key = itemgetter(1))

    #Dictionary of all triples that are shortest paths, not currently used
    # mechanism_dfs = define_path_triples(g_nodes,triples_df,path_nodes,search_type)
    
    return path_nodes

def get_embedding(emb,node):

    embedding_array = emb[str(node)]
    embedding_array = np.array(embedding_array)

    return embedding_array

def convert_path_nodes(path_node,entity_map, embedding_method):

    if embedding_method == "node2vec":
        n = entity_map[path_node]
    # TransE uses node IDs
    elif embedding_method == "transe":
        n = path_node

    return n

def process_path_nodes_value(graph,value,search_algorithm):

    if search_algorithm == "Metapath":
        n = value
    elif search_algorithm == "Shortest_Path":
        n = graph.igraph_nodes[value]
    return n

# For shortest path path_nodes results which are ints to become uris
def convert_to_path_nodes_uris(path_nodes, graph):

    path_nodes_uris = []
    for p in path_nodes:
        new_p = []
        for i in p:
            u = process_path_nodes_value(graph, i, "Shortest_Path")
            new_p.append(u)
        path_nodes_uris.append(new_p)

    return path_nodes_uris

def calc_cosine_sim(emb,entity_map,path_nodes,graph,search_type,kg_type,input_nodes_df, search_algorithm, embedding_method):

    # Handle when no paths were found
    if len(path_nodes[0]) == 0:
        chosen_path_nodes_cs = [[]]
        all_paths_cs_values = []
    elif len(path_nodes[0]) > 1:
        # Set target embedding value to target node if no guiding term is provided and target node is the same for every path
        # Check if target node is the same for every path
        all_identical = all(sublist[-1] == path_nodes[0][-1] for sublist in path_nodes)
        n = process_path_nodes_value(graph,path_nodes[0][len(path_nodes[0])-1],search_algorithm)
        n_int = convert_path_nodes(n, entity_map, embedding_method)
        # n_int = convert_node_for_entity_map(path_nodes[0][len(path_nodes[0])-1],search_algorithm, entity_map)
        target_emb = get_embedding(emb,n_int)

        #Dict of all embeddings to reuse if they exist
        embeddings = defaultdict(list)
        
        #List of lists of cosine similarity for each node in paths of path_nodes, should be same length as path_nodes
        all_paths_cs_values = []
        print("iterating through path_nodes")
        for l in path_nodes:
            cs = []
            # Set target emb to new final node if not all identical
            if not all_identical:
                n1 = process_path_nodes_value(graph,l[-1],search_algorithm)
                n1_int = convert_path_nodes(n1, entity_map, embedding_method)
                target_emb = get_embedding(emb,n1_int)
            range_obj = range(0, len(l) - 1, 2) if search_algorithm == "Metapath" else range(0, len(l) - 1)
            for i in range_obj:
                n1 = process_path_nodes_value(graph,l[i],search_algorithm)
                n1_int = convert_path_nodes(n1, entity_map, embedding_method)
                if n1_int not in list(embeddings.keys()):
                    e = get_embedding(emb,n1_int)
                    embeddings[n1_int] = e
                else:
                    e = embeddings[n1_int]
                cs.append(1 - spatial.distance.cosine(e,target_emb))
            all_paths_cs_values.append(cs)

        #Get sum of all cosine values in value_list
        value_list = list(map(np.mean, all_paths_cs_values))
        chosen_path_nodes_cs = select_max_path(value_list,path_nodes)

    #Will only return 1 dataframe
    # df = define_path_triples(graph,chosen_path_nodes_cs,search_type)
    #Will only return 1 dataframe
    if search_algorithm != "Metapath":
        df = define_path_triples(graph,chosen_path_nodes_cs,search_type)
    else:
        df = define_metapath_triples(chosen_path_nodes_cs)[0]

    df = convert_to_labels(df,graph.labels_all,kg_type,input_nodes_df)

    return df,all_paths_cs_values,chosen_path_nodes_cs[0]

def select_path(value_list,path_nodes):

    #Get max cs from total_cs_path, use that idx of path_nodes then create mechanism
    max_index = value_list.index(max(value_list))
    #Must be list of lists for define_path_triples function
    chosen_path_nodes = [path_nodes[max_index]]

    return chosen_path_nodes

def select_max_path(value_list,path_nodes):

    #Get max value from value_list, use that idx of path_nodes then create mechanism
    max_index = value_list.index(max(value_list))
    #Must be list of lists for define_path_triples function
    chosen_path_nodes = [path_nodes[max_index]]

    return chosen_path_nodes

def convert_to_labels(df,labels_all,kg_type,input_nodes_df):

    all_s = []
    all_p = []
    all_o = []

    if kg_type == 'pkl' or kg_type == "mgmlink":
        for i in range(len(df)):
            try:
                S = input_nodes_df.loc[input_nodes_df['source_id'] == df.iloc[i].loc['S_ID'],'source_label'].values[0]
            except IndexError:
                S = labels_all.loc[labels_all['entity_uri'] == df.iloc[i].loc['S_ID'],'label'].values[0]
            P = labels_all.loc[labels_all['entity_uri'] == df.iloc[i].loc['P_ID'],'label'].values[0]
            try:
                O = input_nodes_df.loc[input_nodes_df['target_id'] == df.iloc[i].loc['O_ID'],'target_label'].values[0]
            except IndexError:
                O = labels_all.loc[labels_all['entity_uri'] == df.iloc[i].loc['O_ID'],'label'].values[0]
            all_s.append(S)
            all_p.append(P)
            all_o.append(O)
    #Need to test for kg-covid19 that S_ID/P_ID/O_ID addition to df works 
    if kg_type == 'kg-covid19' or kg_type == 'kg-microbe':
        for i in range(len(df)):
            try:
                S = input_nodes_df.loc[input_nodes_df['source_id'] == df.iloc[i].loc['S_ID'],'source_label'].values[0]
            except IndexError:
                s_label =  labels_all.loc[labels_all['entity_uri'] == df.iloc[i].loc['S_ID'],'label'].values[0]
                if s_label != "":
                    S = s_label
            P = df.iloc[i].loc['P_ID'].split(':')[-1]
            try:
                O = input_nodes_df.loc[input_nodes_df['target_id'] == df.iloc[i].loc['O_ID'],'target_label'].values[0]
            except IndexError:
                o_label =  labels_all.loc[labels_all['entity_uri'] == df.iloc[i].loc['O_ID'],'label'].values[0]
                if o_label != "":
                    O = o_label 
            all_s.append(S)
            all_p.append(P)
            all_o.append(O)

    df['S'] = all_s
    df['P'] = all_p
    df['O'] = all_o
    #Reorder columns
    df = df.reindex(columns=['S', 'P', 'O', 'S_ID', 'P_ID', 'O_ID'])
    # df = df[['S','P','O','S_ID','P_ID','O_ID']]
    df = df.reset_index(drop=True)
    return df

def convert_to_node_uris(node_pair,graph,kg_type):

    try:
        if node_pair['source_id'] != 'not_needed':
            node1 = node_pair['source_id']
        else:
            node1 = get_uri(graph.labels_all,node_pair['source_label'], kg_type)
    #Handle case where no ID was input for any nodes or only 1 node
    except KeyError: 
        node1 = get_uri(graph.labels_all,node_pair['source_label'], kg_type)
   
    try:
        if node_pair['target_id'] != 'not_needed':
            node2 = node_pair['target_id']
        else:
            node2 = get_uri(graph.labels_all,node_pair['target_label'], kg_type)
    #Handle case where no ID was input for any nodes or only 1 node
    except KeyError:
        node2 = get_uri(graph.labels_all,node_pair['target_label'], kg_type)

    return node1, node2

# Wrapper functions
#Returns the path as a dataframe of S/P/O of all triples' labels within the path
def find_shortest_path(start_node,end_node,graph,g_nodes,labels_all,triples_df,weights,search_type, kg_type):

    node1 = get_uri(labels_all,start_node,kg_type)
    node2 = get_uri(labels_all,end_node,kg_type)

    #Add weights if specified
    if weights:
        w = graph.es["weight"]
    else:
        w = None

    #list of nodes
    path_nodes = graph.get_shortest_paths(v=node1, to=node2, weights=w, mode=search_type)

    df = define_path_triples(g_nodes,triples_df,path_nodes,search_type)

    df = convert_to_labels(df,labels_all,kg_type)

    return df

def get_paths(node_pair,graph,weights,search_type,triples_file,input_dir, output_dir,kg_type, search_algorithm, id_keys_df):

    if search_algorithm == "Shortest_Path":
        path_nodes = find_all_shortest_paths(node_pair,graph,weights,search_type, kg_type)
        id_keys_df = {}
        metapaths_key = {0:''}
    elif search_algorithm == "Metapath":
        path_nodes,id_keys_df,metapaths_key = find_all_metapaths_duckdb(node_pair,graph,kg_type,input_dir,triples_file,id_keys_df)
        metapaths_key_df = pd.DataFrame(list(metapaths_key.items()), columns=['Metapath_Index', 'Metapath'])
        output_folder = output_dir+'/Evaluation_Files'
        #Check for existence of output directory
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        metapaths_key_df.to_csv(output_folder + "/Metapaths_Key.csv",index=False)

    return path_nodes,id_keys_df,metapaths_key

def prioritize_path_cs(path_nodes,input_nodes_df,graph,search_type,emb,entity_map, kg_type, search_algorithm, id_keys_df, embedding_method):

    if len(path_nodes) > 0:
        df,all_paths_cs_values, chosen_path_nodes_cs = calc_cosine_sim(emb,entity_map,path_nodes,graph,search_type, kg_type,input_nodes_df, search_algorithm, embedding_method)
    else:
        df = pd.DataFrame()
        all_paths_cs_values = []
        chosen_path_nodes_cs = []

    return df,all_paths_cs_values,chosen_path_nodes_cs,id_keys_df

def get_metapaths(metapath_filepath):

    # Input metapath template
    metapaths_df = pd.read_csv(metapath_filepath, sep="|")
    path_list = metapaths_df.values.tolist()
    metapaths_df = metapaths_df.replace(METAPATH_SEARCH_MAPS)
    metapaths_list = metapaths_df.values.tolist()

    all_template_list = []
    all_triples_list = []
    # Break metapath into list of lists of triples excluding predicate ([[s,o]])
    for template in path_list:
        template_list = [list(template[i:i+3]) for i in range(0, len(template) - 2, 2) if not isinstance(template[i+1],float)]
        all_template_list.append(template_list)
    for metapath in metapaths_list:
        triples_list = [list(metapath[i:i+3]) for i in range(0, len(metapath) - 2, 2) if not isinstance(template[i+1],float)]
        all_triples_list.append(triples_list)

    return all_template_list, all_triples_list

def path_search_no_prioritization(node_pair, graph, triples_file,input_dir, kg_type, search_algorithm, id_keys_df, path_nodes = 'none'):

    if path_nodes == 'none':
        if search_algorithm == "Shortest_Path":
            path_nodes = find_all_shortest_paths(node_pair,graph,False,'all', kg_type)
        elif search_algorithm == "Metapath" or search_algorithm == "Metapath_Neighbors":
            # Convert node pair into prefixes to search existing metapath files
            # path_nodes = find_all_metapaths_files(node_pair,graph,kg_type,input_dir,triples_file)
            path_nodes,id_keys_df = find_all_metapaths_duckdb(node_pair,graph,kg_type,input_dir,triples_file,id_keys_df,graph.labels_all)

    return path_nodes,id_keys_df

def convert_genes_to_proteins(conn,base_table_name,gene_uri,id_key_df,labels,kg_type):

    # Convert general uri to protein if search metapath_neighbors
    if gene_uri == METAPATH_SEARCH_MAPS["gene"]:
        protein = METAPATH_SEARCH_MAPS["protein"]

    else:
        # Remove special characters from uri since duckdb doesn't handle them
        gene_id = re.search(r'http://(.*)', gene_uri).group(1)
        gene_tag = gene_id.replace("/","_").replace(".","_")

        create_subject_object_pair_table(
                conn,
                table_name = "gene_match", #gene_tag+"_protein",
                base_table_name = base_table_name,
                subject = "gene", #gene_tag,
                object = "PR",
                subject_prefix = "%" + gene_id,
                predicate_prefix = "%RO_0002205%",
                object_prefix = "%PR_%"
            )

        result = conn.execute(
            f"""
            SELECT "gene","PR" FROM gene_match;
            """
        ).fetchall()

        # Replace IDs with labels so that they can later on be matched to final mechanism to ensure Extra/Original nodes are labeled
        result_list = [list(t) for t in result]
        for r in result_list:
            s = r[0]
            o = r[1]
            s_label = get_label(labels,s,kg_type)
            o_label = get_label(labels,o,kg_type)
            r[0] = s_label
            r[1] = o_label

        # ct = get_table_count(conn, "gene_match")
        result_df = pd.DataFrame(result_list, columns = ["Original","New"])
        id_key_df = pd.concat([id_key_df, result_df], ignore_index=True)
        protein = result[0][1]

        drop_table(conn, "gene_match")

    return protein,id_key_df

def find_all_metapaths_duckdb(node_pair,graph,kg_type,input_dir,triples_list_file,id_keys_df):

    metapaths_list,original_metapaths_list = get_all_input_metapaths(input_dir,node_pair)

    # List of each metapath by the given triples, eg: [[['NCBITaxon', '%', 'CHEBI'], ['CHEBI', '%', 'MONDO']]]
    triples_list = []
    for metapath in metapaths_list:
        l = [list(metapath[i:i+3]) for i in range(0, len(metapath) - 2, 2) if not isinstance(metapath[i+1],float)]
        triples_list.append(l)

    # print("triples_list")
    # print(triples_list)

    # List of paths found that match metapaths, will match length of filtered_metapaths
    # all_paths_found = []
    all_metapaths_results = []
    metapaths_key = {}

    # Create a DuckDB connection
    conn = duckdb.connect(":memory:")
    conn.execute("PRAGMA memory_limit='64GB'")

    duckdb_load_table(conn, triples_list_file, "edges", ["subject", "predicate", "object"])

    node1, node2 = convert_to_node_uris(node_pair,graph,kg_type)
    if node1 is None or node2 is None:
        path_nodes = [[]]

    else:
        print("search duckdb")

        # Doing this using Duckdb

        # First only get metapaths that match the input nodes
        # Filter the metapaths based on the first and last values, eg: [[['NCBITaxon', '%', 'CHEBI'], ['CHEBI', '%', 'MONDO']]]
        filtered_metapaths = [m for m in triples_list if m[0][0] in node1 and m[-1][-1] in node2]
        # print("filtered_metapaths")
        # print(filtered_metapaths)

        # Search existing metapaths by node pair/triple to return [[source,target]] pairs
        # Go through each metapath that matches node1, node2
        for m_idx, m in enumerate(filtered_metapaths):
            print(m)
            # List of each paired table found with duckdb, eg: CHEBI_MONDO:XX, UniprotKB:MONDO:XX
            tables = []
            # List of paths found that match metapaths, will match length of m
            all_path_nodes = []
            all_paths_found = []
            # Remove used tables from previous metapath
            try:
                del next_base_table_name
            except UnboundLocalError:
                pass
            # Go through each triple that is in the metapath
            for i, (s, p, o) in enumerate(m):
                # print(i)
                #if get_metapath_key(node1) == s and get_metapath_key(node2) == o:
                # For last tables paired, use final node2 and previous filtered tables
                if i == len(m) - 1:
                    # read in table with this protein as s or o, r, and and PR_ as o or s
                    t_name = "_".join([re.sub(r'[/_]', '', s+"|"+str(i-1)),re.sub(r'[/_]', '', node2+"|"+str(i))])
                    new_table_name = create_filtered_subject_object_pair_table(
                        conn,
                        base_table_name = "edges",
                        compared_table_name = next_base_table_name,
                        output_table_name = t_name,
                        subject = re.sub(r'[/_]', '', s+"|"+str(i-1)),
                        object = re.sub(r'[/_]', '', node2+"|"+str(i)),
                        subject_prefix = "%" + s + "%",
                        predicate_prefix = "%" + p + "%",
                        object_prefix = "%" + node2 + "%"
                    )

                    ct = get_table_count(conn, t_name)
                    # print("num paths last triple: ",s,node2,ct)

                    if ct > 0:
                        tables.append(t_name)

                    if ct == 0:
                        drop_table(conn, t_name)
                        # read in table with this protein as s or o, r, and and PR_ as o or s
                        t_name = "_".join([re.sub(r'[/_]', '', node2),re.sub(r'[/_]', '', s+"|"+str(i))])
                        new_table_name = create_filtered_subject_object_pair_table(
                            conn,
                            base_table_name = "edges",
                            compared_table_name = next_base_table_name,
                            output_table_name = t_name,
                            subject = re.sub(r'[/_]', '', node2+"|"+str(i)),
                            object = re.sub(r'[/_]', '', s+"|"+str(i-1)),
                            subject_prefix = "%" + node2 + "%",
                            predicate_prefix = "%" + p + "%",
                            object_prefix = "%" + s + "%"
                        )

                        ct = get_table_count(conn, t_name)
                        # print("num paths last triple: ",node2,s,ct)

                        if ct > 0:
                            tables.append(t_name)

                        if ct == 0:
                            drop_table(conn, t_name)

                # For first tables paired, create original object pair table
                elif i == 0:
                    # read in table with this protein as s or o, r, and and PR_ as o or s
                    t_name = "_".join([re.sub(r'[/_]', '', node1),re.sub(r'[/_]', '', o+"|"+str(i))])
                    new_table_name = create_subject_object_pair_table(
                        conn,
                        table_name = t_name,
                        base_table_name = "edges",
                        subject = re.sub(r'[/_]', '', node1),
                        object = re.sub(r'[/_]', '', o+"|"+str(i)),
                        subject_prefix = "%" + node1 + "%",
                        predicate_prefix = "%" + p + "%",
                        object_prefix = "%" + o + "%"
                    )

                    ct = get_table_count(conn, t_name)
                    # print("num paths first triple: ",node1,o,ct)

                    if ct > 0:
                        tables.append(t_name)
                        next_base_table_name = new_table_name
                    
                    if ct == 0:
                        drop_table(conn, t_name)
                        # read in table with this protein as s or o, r, and and PR_ as o or s
                        t_name = "_".join([re.sub(r'[/_]', '', o),re.sub(r'[/_]', '', node1+"_"+str(i))])
                        new_table_name = create_subject_object_pair_table(
                            conn,
                            table_name = t_name,
                            base_table_name = "edges",
                            subject = re.sub(r'[/_]', '', o+"|"+str(i)),
                            object = re.sub(r'[/_]', '', node1),
                            subject_prefix = "%" + o + "%",
                            predicate_prefix = "%" + p + "%",
                            object_prefix = "%" + node1 + "%"
                        )

                        ct = get_table_count(conn, t_name)
                        # print("num paths first triple: ",o+"|"+str(i),node1,ct)
                        if ct > 0:
                            tables.append(t_name)
                            next_base_table_name = new_table_name

                # For middle tables paired, use previous subject and object pairs and filtered table
                else:
                    try:
                        t_name = "_".join([re.sub(r'[/_]', '', s+"|"+str(i-1)),re.sub(r'[/_]', '', o+"|"+str(i))])
                        new_table_name = create_filtered_subject_object_pair_table(
                                conn,
                                base_table_name = "edges",
                                compared_table_name = next_base_table_name,
                                output_table_name = t_name,
                                subject = re.sub(r'[/_]', '', s+"|"+str(i-1)),
                                object = re.sub(r'[/_]', '', o+"|"+str(i)),
                                subject_prefix = "%" + s + "%",
                                predicate_prefix = "%" + p + "%",
                                object_prefix = "%" + o + "%"
                            )
                    # Handle when there was no result for the first pair
                    except UnboundLocalError:
                        try:
                            drop_table(conn, new_table_name)
                        except duckdb.CatalogException as e:
                            pass
                        break

                    ct = get_table_count(conn, t_name)
                    # print("num paths middle triple: ",s,o,ct)

                    if ct > 0:
                        tables.append(t_name)
                        next_base_table_name = new_table_name
                    
                    if ct == 0:
                        drop_table(conn, t_name)
                        # read in table with this protein as s or o, r, and and PR_ as o or s
                        t_name = "_".join([re.sub(r'[/_]', '', o+"|"+str(i)),re.sub(r'[/_]', '', s+"|"+str(i-1))])
                        new_table_name = create_filtered_subject_object_pair_table(
                            conn,
                            base_table_name = "edges",
                            compared_table_name = next_base_table_name,
                            output_table_name = t_name,
                            subject = re.sub(r'[/_]', '', o+"|"+str(i)),
                            object = re.sub(r'[/_]', '', s+"|"+str(i-1)),
                            subject_prefix = "%" + o + "%",
                            predicate_prefix = "%" + p + "%",
                            object_prefix = "%" + s + "%"
                        )

                        ct = get_table_count(conn, t_name)
                        # print("num paths middle triple: ",o,s,ct)
                        if ct > 0:
                            tables.append(t_name)
                            next_base_table_name = new_table_name

            # print("tables")
            # print(tables)

            tables_paired = [list(pair) for pair in zip(tables, tables[1:])] if len(tables) > 1 else tables

            # print("tables_paired")
            # print(tables_paired)

            # Confirm that values were found for each triple in metapath, ex: [['NCBITaxon:165179_CHEBI', 'CHEBI_MONDO:0005180']]
            # print("len m -1: ", len(m) - 1)
            if len(tables_paired) < (len(m) - 1):
                all_tables = [item for sublist in tables_paired for item in sublist]
                all_tables = list(set(all_tables))
                for t in all_tables:
                    drop_table(conn, t)
                # # except duckdb.CatalogException as e:
                # #     pass
                path_nodes = []
            elif len(tables_paired) == 1:
                query = (
                        f"""
                        SELECT * FROM '{tables_paired[0]}';
                        """
                    )

                result = conn.execute(query).fetchall()
                # print(query)
                # print(result)

                # Returns path from the given triple t
                path_nodes = conn.execute(query).df().values.tolist()
                all_path_nodes.append(path_nodes)
            else:
                # Get complete metapaths
                for t in tables_paired:
                    # List of path nodes for given triple
                    # triples_path_nodes = []
                    # print(t)
                    # Compare over the prefix that matches
                    t_prefixes = [s.split("_") for s in t] #re.sub(r'\d+', '', s) re.sub(r'\|.*$', '', s).split('_')
                    # print(t_prefixes)
                    comparison_prefix = list(set(t_prefixes[0]) & set(t_prefixes[1]))[0]
                    # print("comparison_prefix: ",comparison_prefix)
                    # Handle case where s and o are unique
                    if len(set(t_prefixes[0])) == 2:
                        # subject_prefix = [i for i in re.sub(r'\|.*$','',t[0]).split("_") if i != comparison_prefix][0]
                        subject_prefix = [i for i in t[0].split("_") if i != comparison_prefix][0]
                    elif len(set(t_prefixes[0])) == 1:
                        # subject_prefix = [i for i in re.sub(r'\|.*$','',t[0]).split("_")][0]
                        subject_prefix = [i for i in t[0].split("_")][0]
                    if len(set(t_prefixes[1])) == 2:
                        # object_prefix = [i for i in re.sub(r'\|.*$','',t[1]).split("_") if i != comparison_prefix][0]
                        object_prefix = [i for i in t[1].split("_") if i != comparison_prefix][0]
                    elif len(set(t_prefixes[1])) == 1:
                        # object_prefix = [i for i in re.sub(r'\|.*$','',t[1]).split("_")][0]
                        object_prefix = [i for i in t[1].split("_")][0]

                    join_tables_subject_object(
                        conn, 
                        base_table_name = t[1], 
                        compared_table_name = t[0], 
                        output_table_name = "full_metapath",
                        output_subject = subject_prefix, #t[0].split("_")[0], 
                        output_object = object_prefix, #t[1].split("_")[1], 
                        comparison = comparison_prefix #t[0].split("_")[1]
                    )

                    ct = get_table_count(conn, "full_metapath")
                    # print("full_metapath: ",ct)

                    query = (
                        f"""
                        SELECT * FROM full_metapath;
                        """
                    )

                    result = conn.execute(query).fetchall()
                    # print(query)
                    # print(result)

                    # Returns path from the given triple t
                    path_nodes = conn.execute(query).df().values.tolist()
                    all_path_nodes.append(path_nodes)
                    print(len(all_path_nodes))

                    drop_table(conn, "full_metapath")
                    # try:
                    #     drop_table(conn, t[0])
                    # except duckdb.CatalogException as e:
                    #     pass
            
            # When more than 2 triples were involved, need to combine by object/subject aligning prefixes
            try:
                drop_table(conn, t[1])
            except duckdb.CatalogException as e:
                pass
            # print("before combining")
            # print(len(all_path_nodes))
            # print(all_path_nodes)
            if len(all_path_nodes) > 0:
                recursive_path_result = recursive_path_combination(all_path_nodes, tables_paired)
                all_paths_found.extend(recursive_path_result)
                # print("after combining: ",m)
                # print(len(recursive_path_result))
                # print("len all_paths_found")
                # print(len(all_paths_found))
            else:
                all_paths_found = []
                # print("after combining: ",m)

            all_metapaths_results.append(all_paths_found)
            # print("len all_metapaths_results: ")
            # print(len(all_metapaths_results))
            metapaths_key[m_idx] = '_'.join([item for item in original_metapaths_list[m_idx] if not (isinstance(item, float))]) #original_metapaths_list[m_idx])

    print("after combining all")
    print(len(all_metapaths_results))
    # Don't know why this is necessary, removed for now
    # all_path_nodes = sorted(all_path_nodes,key = itemgetter(1))
    
    if len(all_metapaths_results) == 0:
        # all_paths_found = [[]]
        all_metapaths_results = [[] for _ in range(len(filtered_metapaths))]

    return all_metapaths_results,id_keys_df,metapaths_key

def get_all_input_metapaths(input_dir,node_pair):
    """
    Args:
        input_dir (str): Input directory

    Returns:
        list: list of metapaths as triples
    """

    # Different metapaths for different case studies
    if "faecalibacterium" in node_pair:
        metapaths_file = input_dir+'/metapaths/Input_Metapaths.csv'
    else:
        metapaths_file = input_dir+'/metapaths/Input_Metapaths_Long.csv'
    # Get list of triples in metapath by prefix, e.g. [['PR_', '', 'CHEBI_'], ['CHEBI_', '', 'MONDO_']]
    # Input metapath template
    metapaths_df = pd.read_csv(metapaths_file, sep="|")
    original_metapaths_list = metapaths_df.values.tolist()
    metapaths_df = metapaths_df.replace(METAPATH_SEARCH_MAPS)
    metapaths_list = metapaths_df.values.tolist()

    return metapaths_list, original_metapaths_list

def recursive_path_combination(all_path_nodes,tables_paired):

    if len(all_path_nodes) == 1:
        return all_path_nodes[0]
    
    # Apply function to first 2 elements
    result = combine_paths_in_metapath(all_path_nodes[0:2],tables_paired[0:2])

    # Previous tables_paired value will cover the result from last function call
    return recursive_path_combination([result] + all_path_nodes[2:],tables_paired[1:])

def combine_paths_in_metapath(all_path_nodes,tables_paired):
    
    combined_path_nodes = []

    for i in range(len(tables_paired)-1):
        # Get common paired tables between 2 subpaths or combined triples
        common_paired_table = list(set(tables_paired[i]) & set(tables_paired[i+1]))[0]
        prefixes = common_paired_table.split("_")
        prefixes = [re.sub(r'\|.*$', '', i) for i in prefixes]
        # Fix gene prefix
        prefixes = ["/gene/" if x == "gene" else x for x in prefixes]
        # Get paths from each table pair
        starting_paths = all_path_nodes[i]
        ending_paths = all_path_nodes[i+1]
        # print("common_paired_table: ")
        # print(common_paired_table)
        # print("prefixes: ")
        # print(prefixes)
        for s_p in starting_paths:
            overlapping_start_prefixes = [value for value in s_p if any(prefix in value for prefix in prefixes)]
            for e_p in ending_paths:
                overlapping_end_prefixes = [value for value in e_p if any(prefix in value for prefix in prefixes)]
                common_values = [val for val in overlapping_start_prefixes if val in overlapping_end_prefixes]
                if len(common_values) == len(prefixes):
                    # Find the indices of the common values in the list
                    start_index = e_p.index(common_values[0]) if common_values[0] in e_p else -1
                    end_index = e_p.index(common_values[-1]) if common_values[-1] in e_p else -1

                    # Remove elements from start_index to end_index inclusive
                    if start_index != -1 and end_index != -1 and start_index <= end_index:
                        filtered_data = e_p[:start_index] + e_p[end_index + 1:]
                        new_path = s_p + filtered_data
                        combined_path_nodes.append(new_path)

    # print(tables_paired)
    # print(len(combined_path_nodes))
    return combined_path_nodes
