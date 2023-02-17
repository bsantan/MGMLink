import pandas as pd
import re
import os
import copy

# set column number and width to display all information
pd.set_option('display.max_rows', None)



# Read in the user example file and output as a pandas dataframe
def read_user_input(user_example_file):
	examples = pd.read_csv(user_example_file, sep= "|")
	return(examples)

# Get list of unique nodes
# Inputs:	examples		pandas dataframe of user input examples.
# Outputs:	nodes 			set of unique nodes
def unique_nodes(examples):
	# get unique node values
	nodes = list(set(pd.melt(examples)["value"].values))
	return(nodes)

# Search through labels to find nodes based on input feature
# Inputs: 	node 		string for user input example.
#			kg			knowledge graph of class Knowledge Graph
#			ontology	specific ontology to restrict search of nodes

def find_node(node, kg, kg_type, ontology = ""):
	nodes = kg.labels_all
	#MGMLink has a different layout of the labels file
	if kg_type == 'mgmlink':
		results = nodes[nodes['label'] == node][["label", "entity_uri"]]
		#results = nodes[nodes["label"].str.contains(node,flags=re.IGNORECASE, na = False)][["label", "entity_uri"]]
	else:
		### All caps input is probably a gene or protein. Either search in a case sensitive manner or assign to specific ontology.
		if node.isupper(): #likely a gene or protein
			results = nodes[(nodes["label"].str.contains(node,flags=re.IGNORECASE, na = False)|nodes["synonym"].str.contains(node,flags=re.IGNORECASE, na = False)|nodes["description/definition"].str.contains(node,flags=re.IGNORECASE, na = False)) & nodes["entity_uri"].str.contains("gene|PR|GO",flags=re.IGNORECASE, na = False) ][["label", "entity_uri"]]
		else:
			results = nodes[nodes["label"].str.contains(node,flags=re.IGNORECASE, na = False)|nodes["synonym"].str.contains(node,flags=re.IGNORECASE, na = False)|nodes["description/definition"].str.contains(node,flags=re.IGNORECASE, na = False)][["label", "entity_uri"]]

	return(results)
                

# Create a list of nodes for input

# Could potentially find several features for a single input example. Need a way to be able to select multiple feaures for a search. 
# Need a way to go back through search terms. 

def search_nodes(nodes, kg, examples,kg_type):
	examples["source_label"] = ""
	examples["target_label"] = ""
	for node in nodes:
		node_orig = copy.deepcopy(node)
		search_loop = True
		while(search_loop):
			print("User Search Node: ", node)
			found_nodes = find_node(node,kg,kg_type)
			nrow = found_nodes.shape[0]
			if nrow == 0:
				print("No search terms returned")
				node = input("Please try another input term: ")
			else:
				search_loop = False
		print("Found", nrow, "features in KG")
		user_input = ""
		bad_input = True
	
		if nrow < 20:
			while(bad_input):
				print(found_nodes.iloc[0:nrow,].to_string())
				user_input = input("Input node'label': ")
				if node_in_search(found_nodes,user_input):
					#Manage if there are 2 duplicate label names
					if len(found_nodes[found_nodes['label'] == user_input][['label','entity_uri']]) > 1:
						user_input = input("Input node 'id': ")
						if node_id_in_search(found_nodes,user_input):
							node_label = kg.labels_all.loc[kg.labels_all['id'] == user_input,'label'].values[0]
							bad_input = False
					else:
						node_label= user_input
						bad_input = False
				elif node_in_labels(kg,user_input):
					node_label= user_input
					bad_input = False
				else:
					print("Input not in search results.... try again")
		else:	
			i = 0
			while(bad_input):
				high = min(nrow,(i+1)*20)
				print(found_nodes.iloc[i*20:high,].to_string())
				user_input = input("Input node 'label' or 'f' for the next 20 features or 'b' for the previous 20: ")
				if user_input == 'f':
					i+=1
				elif user_input == 'b':
					i-=1
				else:
					i+=1
					if node_in_search(found_nodes,user_input):
						node_label = user_input
						bad_input = False
					else:
						print("Input not in search results.... try again")
		print('node_label: ',node,node_label)
		examples.loc[examples["source"] == node_orig,"source_label"] = node_label
		examples.loc[examples["target"] == node_orig,"target_label"] = node_label
	return(examples)


# Check if search input is in the list of integer_ids
def node_in_search(found_nodes, user_input):
	if user_input in found_nodes[["label"]].values:
		return(True)
	else:
		return(False)

# Check if search input is in the list of integer_ids
def node_id_in_search(found_nodes, user_input):
	if user_input in found_nodes[["id"]].values:
		return(True)
	else:
		return(False)

# Check if search input is in the all nodes
def node_in_labels(kg, user_input):
	labels = kg.labels_all

	if user_input in labels[["label"]].values:
		return(True)
	else:
		return(False)

#subgraph_df is a dataframe with source,targe headers and | delimited
def create_input_file(examples,output_dir):
    input_file = output_dir+"/_Input_Nodes_.csv"
    #examples = examples[["source_label","target_label"]]
    #examples.columns = ["source", "target"]
    examples.to_csv(input_file, sep = "|", index = False)



# Check if the input_nodes file already exists
def check_input_existence(output_dir):
    exists = 'false'
    mapped_file = ''
    for fname in os.listdir(output_dir):
        if bool(re.match("_Input_Nodes_",fname)):
            exists = 'true'
            mapped_file = fname
    return exists,mapped_file



# Wrapper function
def interactive_search_wrapper(g,user_input_file, output_dir,kg_type):
	exists = check_input_existence(output_dir)
	if(exists[0] == 'false'):
		print('Interactive Node Search')
		#Interactively assign node
		u = read_user_input(user_input_file)
		n = unique_nodes(u)
		print('nodes: ',n)
		s = search_nodes(n,g,u,kg_type)
		create_input_file(s,output_dir)
	else:
		print('Node mapping file exists... moving to embedding creation')
		mapped_file = output_dir + '/'+ exists[1]
		s = pd.read_csv(mapped_file, sep = "|")
	return(s)