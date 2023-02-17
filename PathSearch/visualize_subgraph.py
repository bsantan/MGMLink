from assign_nodes import unique_nodes
import pandas as pd
import csv
import py4cytoscape as p4c
from py4cytoscape import gen_node_color_map
from py4cytoscape import palette_color_brewer_d_RdBu
import os

#subgraph_df is a dataframe with S, P, O headers and | delimited
def create_node_attributes(input_nodes_df,subgraph_df):
    
    original_nodes = unique_nodes(input_nodes_df)
        
    full_list = []

    for i in range(len(subgraph_df)):
        #Only add subject and object columns, not the predicate
        for col in [0,2]:
            l = []
            node = subgraph_df.iloc[i,col]
            if node in original_nodes:
                att = 'Mechanism'
            else:
                att = 'Extra'
            l.append(node)
            l.append(att)
            full_list.append(l)
    
    subgraph_attribute_df = pd.DataFrame(full_list,columns = ['Node','Attribute'])
    
    subgraph_attribute_df = subgraph_attribute_df.drop_duplicates(subset=['Node'])
    subgraph_attribute_df = subgraph_attribute_df.reset_index(drop=True)
    
    return subgraph_attribute_df

#subgraph_df is a dataframe with S, P, O headers and | delimited
def create_noa_file(subgraph_attribute_df,output_dir):

    noa_file = output_dir+"/Subgraph_attributes.noa"
    #Check for existence of output directory
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    l = subgraph_attribute_df.values.tolist()

    with open(noa_file, "w", newline="") as f:
        writer = csv.writer(f,delimiter='|')
        writer.writerow(["Node","Attribute"])
        writer.writerows(l)

def create_sif_file(subgraph_df,output_dir):

    sif_file = output_dir+"/Subgraph.csv"
    #Check for existence of output directory
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    subgraph_df.to_csv(sif_file,sep='|',index=False)

#subgraph_df is a dataframe with S, P, O headers and | delimited
def create_cytoscape_png(subgraph_df,subgraph_attributes_df,output_dir):

    png_file = output_dir+'/Subgraph_Visualization.png'
    #Check for existence of output directory
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    #Update column names for cytoscape
    subgraph_df.columns = ['source','interaction','target']
    subgraph_attributes_df.columns = ['id','group']

    p4c.create_network_from_data_frames(subgraph_attributes_df,subgraph_df,title='subgraph')

    #Ensure no network exists named subgraph in Cytoscape or you will have to manually override before it can be output
    p4c.set_visual_style('BioPAX_SIF',network='subgraph')

    p4c.set_node_color_mapping(**gen_node_color_map('group', mapping_type='d',style_name='BioPAX_SIF'))

    p4c.set_edge_label_mapping('interaction')
    
    p4c.export_image(png_file,network='subgraph')

# Wrapper Function
def output_visualization(input_nodes_df,subgraph_df,output_dir):

    subgraph_attributes_df = create_node_attributes(input_nodes_df,subgraph_df)

    create_noa_file(subgraph_attributes_df,output_dir)

    create_sif_file(subgraph_df,output_dir)

    create_cytoscape_png(subgraph_df,subgraph_attributes_df,output_dir)

    return subgraph_attributes_df




