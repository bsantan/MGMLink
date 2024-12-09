import pandas as pd
import re
import os
import math
import sys
import glob
import itertools
import numpy as np
import requests
import json
import copy
import csv
from tqdm import tqdm
from itertools import combinations
import copy


#Added here to avoid circular import
def get_label(labels,value,kg_type):
	if kg_type == 'pkl':
		label = labels.loc[labels['entity_uri'] == value,'label'].values[0]
	if kg_type == 'kg-covid19':
		label = labels.loc[labels['id'] == value,'label'].values[0]        
	return label


# Read in the user example file and output as a pandas dataframe
def read_user_input(user_example_file, guiding_term = False):
	if guiding_term:
		examples = pd.read_csv(user_example_file)
		if len(examples.columns) > 1:
			print('Error in format of ' + user_example_file + ', ensure that only "term" column exists in each row.')
			sys.exit(1)
		elif examples.columns[0] != "term":
			print('Error in format of ' + user_example_file + ', ensure that only "term" column exists in each row.')
			sys.exit(1)
		return examples
	
	elif not guiding_term:
		try:
			examples = pd.read_csv(user_example_file, sep= "|")
		#Check for poorly formatted file
		except pd.errors.ParserError:
			print('Error in format of ' + user_example_file + ', ensure that only "source" and "target" columns exist in each row.')
			sys.exit(1)
		#Check for extra columns or blank values or absence of source/target columns
		if (len(examples.columns) != 2) | (examples.isna().values.any()) | (len([item for item in examples.columns if item not in ['source','target']]) > 0):
			print('Error in format of ' + user_example_file + ', ensure that only "source" and "target" columns exist in each row.')
			sys.exit(1)
		return(examples)

def read_ocr_input(user_input_file):
    df = pd.read_csv(user_input_file, sep = "\t")
    if "genes" in user_input_file:
        df = df.loc[df["organism_name"] == "Homo sapiens"]
    return(df)

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

def find_node(node, kg, ontology = ""):

	no_match = True

	# # For microbial nodes
	# microbial = False
	# try_node = "CONTEXTUAL " + node + ": lower digestive tract Homo sapiens"
	# matches,exact_match,no_match = exact_match_identification(kg.labels_all,try_node)
	# if not no_match:
	# 	return matches,exact_match
	# else:

	### Check for exact matches and return only those
	matches,exact_match,no_match = exact_match_identification(kg.labels_all,node)

	#Do not continue if match found
	if not no_match:
		return matches,exact_match

	### For genes check for exact matches by appending (human)
	matches,exact_match,no_match = exact_gene_match_identification(kg.labels_all,node)
	#Do not continue if match found
	if not no_match:
		return matches,exact_match

	# ### Check for exact matches in synonym and return only those
	# matches,exact_match,no_match = exact_synonym_match_identification(kg.labels_all,node)
	# #Do not continue if match found
	# if not no_match:
	# 	return matches,exact_match

	### Fuzzy match
	matches,exact_match,no_match = fuzzy_match_identification(kg.labels_all,node)
	#Do not continue if match found
	if not no_match:
		return matches,exact_match

def exact_match_identification(nodes,node):

	### Check for exact matches and return only those
	exact_matches = nodes[(nodes["label"].str.lower() == node.lower())|(nodes["entity_uri"].str.lower() == node.lower())][["label", "entity_uri"]]
	
	if len(exact_matches) == 1:
		#Return node label if exact match is identified
		node_label = exact_matches.iloc[0][["label"]].values[0]
		exact_match = True
		no_match = False
		return node_label,exact_match,no_match
	#Return full df of exact matches if more than 1
	if len(exact_matches) > 1:
		# For microbes get NCBITaxon ID only
		filtered_matches = exact_matches[exact_matches["entity_uri"].str.contains("NCBITaxon:", case=False)]
		if len(filtered_matches) > 0:
			node_label = filtered_matches.iloc[0][["label"]].values[0]
			exact_match = True
			no_match = False
		else: 
			exact_match = False
			no_match = False
		return node_label,exact_match,no_match

	#Return flag if no exact matches
	else:
		no_match = True
		return "","",no_match

def exact_gene_match_identification(nodes,node):

	### For genes check for exact matches by appending (human)
	human_gene_match = node.lower() + " (human)"
	exact_gene_matches = nodes[(nodes["label"].str.lower() == human_gene_match)][["label", "entity_uri"]]
	
	if len(exact_gene_matches) == 1:
		#Return node label if exact match is identified
		node_label = exact_gene_matches.iloc[0][["label"]].values[0]
		exact_gene_match = True
		no_match = False
		return node_label,exact_gene_match,no_match
	if len(exact_gene_matches) > 1:
		exact_gene_match = False
		no_match = False
		return exact_gene_matches,exact_gene_match,no_match

	#Return flag if no exact matches
	else:
		no_match = True
		return "","",no_match

def exact_synonym_match_identification(nodes,node):

	### Check for exact matches in synonym and return only those, don't assume nodes with special characters is a regex
	exact_synonym_matches = nodes[nodes["synonym"].str.contains(node,flags=re.IGNORECASE, na = False,regex=False)][["label", "entity_uri", "synonym"]]
	if len(exact_synonym_matches) > 0:
		for i in range(len(exact_synonym_matches)):
			synonym_list = exact_synonym_matches.iloc[i].loc["synonym"].split("|")
			synonym_match = [i for i in synonym_list if i.lower() == node.lower()]
			if len(synonym_match) == 1:
				node_label = exact_synonym_matches.iloc[i][["label"]].values[0]
				exact_match = True
				no_match = False
				return node_label,exact_match,no_match

	if len(exact_synonym_matches) > 0:
		exact_match = False
		no_match = False
		return exact_synonym_matches,exact_match,no_match

	#Return flag if no exact matches
	else:
		no_match = True
		return "","",no_match

def fuzzy_match_identification(nodes,node):

	### All caps input is probably a gene or protein. Either search in a case sensitive manner or assign to specific ontology.
	if node.isupper(): #likely a gene or protein
		results = nodes[(nodes["label"].str.contains(node,flags=re.IGNORECASE, na = False,regex=False)) & nodes["entity_uri"].str.contains("gene|PR|GO",flags=re.IGNORECASE, na = False,regex=False) ][["label", "entity_uri"]]
	else:
		results = nodes[nodes["label"].str.contains(node,flags=re.IGNORECASE, na = False,regex=False)][["label", "entity_uri"]]

        # sort results by ontology
	results = results.sort_values(['entity_uri'])

	no_match = False
	exact_match = False
	return results, exact_match, no_match

def map_input_to_nodes(node,kg,enable_skipping):

	search_loop = True
	exact_match = False
	while(search_loop):
		print("User Search Node: ", node)
		found_nodes,exact_match = find_node(node,kg)
		print(found_nodes, exact_match)
		#Handle when node label is returned for exact match, which will be a string not a df
		if isinstance(found_nodes, str):
			search_loop = False	
			nrow = 1
		#Do not require more user input when enable skipping true
		elif enable_skipping:
			nrow = found_nodes.shape[0]
			print("No exact search terms returned, skipping enabled")
			return found_nodes,nrow,exact_match
		else:	
			nrow = found_nodes.shape[0]
			if nrow == 0:
				print("No search terms returned")
				node = input("Please try another input term: ")
			else:
				search_loop = False	
	#print("Found", nrow, "features in KG")

	return found_nodes,nrow,exact_match

def manage_user_input(found_nodes,user_input,kg,exact_match):

	#Only continue search if node_label match not found according to exact_match flag
	if exact_match:
		node_label = found_nodes
		user_id_input = kg.labels_all.loc[kg.labels_all['label'] == node_label]['entity_uri'].values[0]
		bad_input = False
	
	else:
		user_id_input = 'none'
		if node_in_search(found_nodes,user_input):
			#Manage if there are 2 duplicate label names
			if len(found_nodes[found_nodes['label'] == user_input][['label','entity_uri']]) > 1:
				dup_node = True
				while(dup_node):
					#Get all uris with the duplicate labels
					l = found_nodes[found_nodes['label'] == user_input]['entity_uri'].values.tolist()
					print('Select from the following options: ')
					#Show options as numeric, ask for numeric return
					for i in range(len(l)):
						print(str(i+1),': ',l[i])
					option_input = input("Input option #: ")
					if str(int(option_input)-1) in [str(v) for v in range(len(l))]: 
						try:
							#Return the actualy uri not the numeric entry
							user_id_input = l[int(option_input)-1]
						except IndexError: continue
					#Convert uri back to label and store as node_label
					if user_id_input in found_nodes[found_nodes['label'] == user_input]['entity_uri'].values.tolist():
						node_label = kg.labels_all.loc[kg.labels_all['entity_uri'] == user_id_input,'label'].values[0]
						bad_input = False
						dup_node = False

					else:
						print("Input id does not correspond with selected label.... try again")

			else:
				node_label = user_input
				bad_input = False
				dup_node = False

		elif node_in_labels(kg,user_input):
			node_label= user_input
			#Still return node ID even if not needed
			user_id_input = found_nodes[found_nodes['label'] == user_input]['entity_uri'][0]
			bad_input = False
		else:
			print("Input not in search results.... try again")
			node_label = ""
			bad_input = True

	return node_label,bad_input,user_id_input

def search_node(node, kg, examples, enable_skipping, guiding_term = False):

	vals_per_page = 20
	skip_node = False

	bad_input = True
	found_nodes,nrow,exact_match = map_input_to_nodes(node,kg,enable_skipping)
	if exact_match:
		node_label,bad_input,id_given = manage_user_input(found_nodes,found_nodes,kg,exact_match)
	elif not exact_match and enable_skipping:
		skip_node = True
		node_label = ''
		id_given = ''
	else:
		i = 1
		while(bad_input):
			high = min(nrow,(i)*vals_per_page)
			print(found_nodes.iloc[(i-1)*vals_per_page:high,].to_string())
			user_input = input("Input node 'label' or 'f' for the next " + str(vals_per_page) + " features, 'b' for the previous " + str(vals_per_page) + ", or 'u' to update the node search term: ")
			if user_input == 'f':
				if (nrow / i ) > vals_per_page:
					i+=1
			elif user_input == 'b':
				if i > 1:
					i-=1
			elif user_input == 'u':
				#Will replace the original node label in examples file with new one
				examples = examples.replace([node],'REPLACE')
				node = input("Input new node search term: ")
				examples = examples.replace(['REPLACE'],node)
				found_nodes,nrow,exact_match = map_input_to_nodes(node,kg,enable_skipping)
				i = 1
			else:
				node_label,bad_input,id_given = manage_user_input(found_nodes,user_input,kg,exact_match)

	if exact_match:
		#Update node label to be identical to given node
		node_label = node

	return node_label,id_given,examples,skip_node


def create_annotated_df(examples,node,node_label,id_given,guiding_term):

	#examples_new = copy.deepcopy(examples)

	if guiding_term:
		examples.loc[examples["term"] == node,"term_label"] = node_label
		examples.loc[examples["term"] == node,"term_id"] = id_given
	else:
		examples.loc[examples["source"] == node,"source_label"] = node_label
		examples.loc[examples["target"] == node,"target_label"] = node_label
		examples.loc[examples["source"] == node,"source_id"] = id_given
		examples.loc[examples["target"] == node,"target_id"] = id_given

	#print(type(examples.iloc[3].loc['source_label']))
	#examples = examples.replace(np.nan, 'none')

	return examples


# Check if search input is in the list of integer_ids
def node_in_search(found_nodes, user_input):
	if user_input in found_nodes[["label"]].values:
		return(True)
	else:
		return(False)

# Check if search input is in the list of integer_ids
def node_id_in_search(found_nodes, user_input):
	if user_input in found_nodes[["entity_uri"]].values:
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
def create_input_file(examples,output_dir,input_type):
	input_file = output_dir+"/_" + input_type + "_Input_Nodes_.csv"
	
	examples.to_csv(input_file, sep = "|", index = False)

#Takes in a list of skipped nodes for a given pathway
def create_skipped_node_file(skipped_nodes,output_dir,filename=''):
	#Only output file if nodes are skipped
	if len(skipped_nodes) > 0:
		skipped_node_file = output_dir+"/" + filename + "skipped_nodes.csv"
		
		e = open(skipped_node_file,"a")
		e.truncate(0)
		writer = csv.writer(e, delimiter="\t")
		for n in set(skipped_nodes):
			writer.writerow([n])
		e.close()

# Check if the input_nodes file already exists
def check_input_existence(output_dir,input_type):
	exists = 'false'
	mapped_file = ''
	for fname in os.listdir(output_dir):
		if bool(re.match("_" + input_type + "_Input_Nodes_.csv",fname)):
			exists = 'true'
			mapped_file = fname
	return exists,mapped_file

def convert_to_uri(curie):

	if 'gene' in curie.lower():
		uri = PKL_GENE_URI + curie.split(":")[1]
	
	else:
		uri = PKL_OBO_URI + curie.replace(":","_")

	return uri

#Takes cure in the form PREFIX:ID
def normalize_node_api(node_curie):

	url = NODE_NORMALIZER_URL + node_curie

	# Make the HTTP request to NodeNormalizer
	response = requests.get(url, timeout=30)
	response.raise_for_status()

	# Write response to file if it contains data
	entries = response.json()[node_curie]
	try:
		if len(entries) > 1: #.strip().split("\n")
			for iden in entries['equivalent_identifiers']:
				if iden['identifier'].split(':')[0] in PKL_PREFIXES:
					norm_node = iden['identifier']
					return norm_node
	#Handle case where node normalizer returns nothing
	except TypeError:
		return node_curie
	
	else:
		return node_curie


# Wrapper function
def interactive_search_wrapper(g,user_input_file, output_dir, input_type,kg_type,enable_skipping,input_dir="",input_substring=""):
	#Check for existence based on input type
	exists = check_input_existence(output_dir,input_type)
	if enable_skipping:
		skipped_nodes = []
		guiding_term_skipped_nodes = []
	if(exists[0] == 'false'):
			print('Interactive Node Search')
            #Interactively assign node
			if input_type == "experimental_data":
				#Creates examples df without source_label and target_label
				u = read_user_input(user_input_file)
				n = unique_nodes(u)
				u['source_label'] = 'none'
				u['target_label'] = 'none'
				u['source_id'] = 'none'
				u['target_id'] = 'none'
				examples = u
				for node in n:
					node_label,id_given,examples,skip_node = search_node(node,g,u,enable_skipping)
					#Only add node to examples df if not skipped
					if not skip_node:
						examples = create_annotated_df(examples,node,node_label,id_given,False)
					#Drop any triples that contain that node
					elif skip_node:
						'''examples.drop(examples[examples['source'] == node].index, inplace = True)
						examples.drop(examples[examples['target'] == node].index, inplace = True)'''
						u = skip_node_in_edgelist(u,[node])
						skipped_nodes.append(node)
			if input_type == 'literature_comparison' or input_type == 'guiding_term':
				if input_type == 'literature_comparison':
					term_file = input_dir+'/literature_comparison/' + input_substring + '_Literature_Comparison_Terms.csv'
				elif input_type == 'guiding_term':
					term_file = input_dir+'/Guiding_Terms.csv'
				#Creates examples df without source_label and target_label
				u = read_user_input(term_file,True)
				n = unique_nodes(u)
				for node in n:
					node_label,id_given,examples,skip_node = search_node(node,g,u,enable_skipping,True)
					#Only add node to examples df if not skipped
					if not skip_node:
						examples = create_annotated_df(examples,node,node_label,id_given,True)
					#Drop any triples that contain that node
					elif skip_node:
						examples.drop(examples[examples['term'] == node].index, inplace = True)
						guiding_term_skipped_nodes.append(node)

			create_input_file(examples,output_dir,input_type)
			#Creates a skipped_node file per input diagram
			if enable_skipping:
				create_skipped_node_file(skipped_nodes,output_dir)
				create_skipped_node_file(guiding_term_skipped_nodes,output_dir,'guidingTerms')
	else:
		print('Node mapping file exists... moving to embedding creation')
		mapped_file = output_dir + '/'+ exists[1]
		examples = pd.read_csv(mapped_file, sep = "|")
	return(examples)

## dropping a row in the case of self loops based on node ID
def skip_self_loops(input_df):
    for i in range(len(input_df)):
        if input_df.loc[i,"source_id"] == input_df.loc[i,"target_id"]:
            input_df.drop([i], axis = 0, inplace = True)

    return(input_df)

#Takes in a df of the edgelist and a list of all node labels to remove. Edgelist format is source,target columns
def skip_node_in_edgelist(edgelist_df,removed_nodes):

	other_columns = ['source_label','target_label','source_id','target_id']
	#print('Removing nodes')

	for node in removed_nodes:
		#print(node)
		new_edges = []
		node_objects = list(set(edgelist_df.loc[edgelist_df.source == node,'target'].tolist()))
		node_subjects = list(set(edgelist_df.loc[edgelist_df.target == node,'source'].tolist()))
		#Remove self from lists in the case of self loops
		if node in node_objects: node_objects.remove(node)
		if node in node_subjects: node_subjects.remove(node)
		if len(node_objects) > 0 and len(node_subjects) > 0:
			for s in node_subjects:
				for o in node_objects:
					if all(w in edgelist_df.columns.tolist() for w in other_columns):
						s_label = edgelist_df.loc[edgelist_df['source'] == s,'source_label'].values[0]
						o_label = edgelist_df.loc[edgelist_df['target'] == o,'target_label'].values[0]
						s_id = edgelist_df.loc[edgelist_df['source'] == s,'source_id'].values[0]
						o_id = edgelist_df.loc[edgelist_df['target'] == o,'target_id'].values[0]
						new_edges.append([s,o,s_label,o_label,s_id,o_id])
					else:
						new_edges.append([s,o])
		elif len(node_objects) > 1:
			all_pairs = list(combinations(node_objects, 2))
			for i in all_pairs:
				s = list(i)[0]
				o = list(i)[1]
				if all(w in edgelist_df.columns.tolist() for w in other_columns):
					s_label = edgelist_df.loc[edgelist_df['source'] == s,'source_label'].values[0]
					o_label = edgelist_df.loc[edgelist_df['target'] == o,'target_label'].values[0]
					s_id = edgelist_df.loc[edgelist_df['source'] == s,'source_id'].values[0]
					o_id = edgelist_df.loc[edgelist_df['target'] == o,'target_id'].values[0]
					new_edges.append([s,o,s_label,o_label,s_id,o_id])
				else:
					new_edges.append([s,o])
		elif len(node_subjects) > 1:
			all_pairs = list(combinations(node_subjects, 2))
			for i in all_pairs:
				s = list(i)[0]
				o = list(i)[1]
				#All node_subjects can be indexed to row that contains them as a subject
				if all(w in edgelist_df.columns.tolist() for w in other_columns):
					s_label = edgelist_df.loc[edgelist_df['source'] == s,'source_label'].values[0]
					o_label = edgelist_df.loc[edgelist_df['source'] == o,'source_label'].values[0]
					s_id = edgelist_df.loc[edgelist_df['source'] == s,'source_id'].values[0]
					o_id = edgelist_df.loc[edgelist_df['source'] == o,'source_id'].values[0]
					new_edges.append([s,o,s_label,o_label,s_id,o_id])
				else:
					new_edges.append([s,o])
		#Remove triples with node
		edgelist_df = edgelist_df.drop(edgelist_df.loc[edgelist_df['source'] == node].index)
		edgelist_df = edgelist_df.drop(edgelist_df.loc[edgelist_df['target'] == node].index) #, inplace=True).reset_index(drop=True)
		edgelist_df = edgelist_df.reset_index(drop=True)
		#Add new triples to edgelist
		if len(new_edges) > 0:
			new_triples_df = pd.DataFrame(new_edges, columns = edgelist_df.columns.tolist())
			edgelist_df = pd.concat([edgelist_df,new_triples_df], axis=0)
			edgelist_df = edgelist_df.reset_index(drop=True)

	#Remove duplicate node pairs that are in different order
	edgelist_df = edgelist_df.groupby(edgelist_df.apply(frozenset, axis=1), as_index=False).first()

	return edgelist_df

	

	