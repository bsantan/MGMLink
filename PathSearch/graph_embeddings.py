from collections import defaultdict
import os
import pickle
from gensim.models import Word2Vec
from gensim.models import KeyedVectors
import json
import re
from grape import Graph
from grape.embedders import TransEEnsmallen

import pandas as pd

class Embeddings:

    def __init__(self, triples_file,labels_file,input_dir,embedding_dimensions, kg_type):
        self.triples_file = triples_file
        self.labels_file = labels_file
        self.input_dir = input_dir
        self.embedding_dimensions = embedding_dimensions
        self.kg_type = kg_type

    def check_file_existence(self,embeddings_file):
        exists = 'false'
        for fname in os.listdir(self.input_dir):
            if bool(re.search(embeddings_file, fname)):
                exists = 'true'
        return exists
        
    def generate_node2vec_graph_embeddings(self,base_name):

        # base_name = self.triples_file.split('/')[-1]
    
        embeddings_file = base_name.split('.')[0] + '_node2vec_Embeddings.emb' # + str(self.embedding_dimensions) + '.emb'
       
        #Check for existence of embeddings file
        exists = self.check_file_existence(embeddings_file)

        if exists == 'true':
            emb = KeyedVectors.load_word2vec_format(self.input_dir + '/' + embeddings_file, binary=False)
            entity_map = json.load(open(self.input_dir + '/' + base_name.replace('Triples_Identifiers','Triples_Integer_Identifier_Map')))
        #Only generate embeddings if file doesn't exist
        if exists == 'false':
            if self.kg_type == 'pkl' or self.kg_type == 'mgmlink':
                output_ints_location = self.input_dir + '/' + base_name.replace('Triples_Identifiers','Triples_Integers_node2vecInput')
                output_ints_map_location = self.input_dir + '/' + base_name.replace('Triples_Identifiers','Triples_Integer_Identifier_Map')
            if self.kg_type == 'kg-covid19':
                output_ints_location = self.input_dir + '/' + base_name.replace('edges','Triples_Integers_node2vecInput')

                output_ints_map_location = self.input_dir + '/' + base_name.replace('edges','Triples_Integer_Identifier_Map')

            with open(self.triples_file, 'r') as f_in:
                if self.kg_type == 'pkl' or self.kg_type == 'mgmlink':
                    kg_data = set(tuple(x.replace('>','').replace('<','').split('\t')) for x in f_in.read().splitlines())
                    f_in.close()
                if self.kg_type == 'kg-covid19':
                    kg_data = set(tuple(x.split('\t'))[1:4] for x in f_in.read().splitlines())
                    f_in.close()
            entity_map = {}
            entity_counter = 0
            graph_len = len(kg_data)
             
            ints = open(output_ints_location, 'w', encoding='utf-8')
            ints.write('subject' + '\t' + 'predicate' + '\t' + 'object' + '\n')

            for s, p, o in kg_data:
                subj, pred, obj = s, p, o
                if subj not in entity_map: entity_counter += 1; entity_map[subj] = entity_counter
                if pred not in entity_map: entity_counter += 1; entity_map[pred] = entity_counter
                if obj not in entity_map: entity_counter += 1; entity_map[obj] = entity_counter
                ints.write('%d' % entity_map[subj] + '\t' + '%d' % entity_map[pred] + '\t' + '%d' % entity_map[obj] + '\n')
            ints.close()

                #write out the identifier-integer map
            with open(output_ints_map_location, 'w') as file_name:
                json.dump(entity_map, file_name)

            with open(output_ints_location) as f_in:
                kg_data = [x.split('\t')[0::2] for x in f_in.read().splitlines()]
                f_in.close()

                #print('node2vecInput_cleaned: ',kg_data)
            if self.kg_type == 'pkl' or self.kg_type == 'mgmlink':
                file_out = self.input_dir + '/' + base_name.replace('Triples_Identifiers','Triples_node2vecInput_cleaned')
            if self.kg_type == 'kg-covid19':
                file_out = self.input_dir + '/' + base_name.replace('edges','Triples_node2vecInput_cleaned')                   

            with open(file_out, 'w') as f_out:
                for x in kg_data[1:]:
                    f_out.write(x[0] + ' ' + x[1] + '\n')
                f_out.close()
                
                
            embeddings_out = self.input_dir + '/' + embeddings_file

            command = "python sparse_custom_node2vec_wrapper.py --edgelist {} --dim {} --walklen 10 --walknum 20 --window 10 --output {}"
            os.system(command.format(file_out,self.embedding_dimensions, embeddings_out ))

            exists = self.check_file_existence(embeddings_file)

                #Check for existence of embeddings file and error if not
            if exists == 'false':
                raise Exception('Embeddings file not generated in output directory: ' + self.input_dir + '/' + embeddings_file)   


            emb = KeyedVectors.load_word2vec_format(self.input_dir + '/' + embeddings_file, binary=False)

        return emb, entity_map
    
    def generate_grape_graph(self):

        grape_graph = Graph.from_csv(
                # Edges related parameters

                ## The path to the edges list tsv
                edge_path=self.triples_file,
                ## Set the tab as the separator between values
                edge_list_separator="\t",
                ## The first rows should NOT be used as the columns names
                edge_list_header=True,
                edge_list_edge_types_column_number = 1,
                ## The source nodes are in the first nodes
                sources_column_number=0,
                ## The destination nodes are in the second column
                destinations_column_number=2,
                ## Both source and destinations columns use numeric node_ids instead of node names
                edge_list_numeric_node_ids=False,

                # Nodes related parameters
                ## The path to the nodes list tsv
                node_path=self.labels_file,
                ## Set the tab as the separator between values
                node_list_separator="\t",
                ## The first rows should be used as the columns names
                node_list_header=True,
                ## The column with the node names is the one with name "node_name".
                nodes_column="Identifier",

                # Graph related parameters
                ## The graph is undirected
                directed=True,
                ## The name of the graph is HomoSapiens
                name="MGMLink",
                ## Display a progress bar, (this might be in the terminal and not in the notebook)
                verbose=True,
            )
        
        return grape_graph

    def generate_grape_graph_embeddings(self,base_name,embedding_method):

        embeddings_file = base_name.split('.')[0] + '_' + embedding_method + '_Embeddings.pkl' # + str(self.embedding_dimensions) + '.emb'

        #Check for existence of embeddings file
        exists = self.check_file_existence(embeddings_file)

        if exists == 'true':
            with open(embeddings_file, 'rb') as file:
                # Use the 'rb' mode to read in binary mode
                embedding_model = pickle.load(file)
        #Only generate embeddings if file doesn't exist
        if exists == 'false':
            mgmlink = self.generate_grape_graph()
            if embedding_method == "transe":
                model = TransEEnsmallen(embedding_size=self.embedding_dimensions)
            # elif embedding_method == "rotate":
            #     model = RotatEPyKEEN(embedding_size=self.embedding_dimensions)
            embedding_model = model.fit_transform(mgmlink)

        embedding_model_df = pd.DataFrame(embedding_model._node_embeddings[0])
        emb = defaultdict(list)
        for i,row in embedding_model_df.iterrows():
            emb[i.replace("<","").replace(">","")] = row.tolist()
        entity_map = {}

        return emb, entity_map

    def generate_graph_embeddings(self,embedding_method):

        base_name = self.triples_file.split('/')[-1]
    
        if embedding_method == "node2vec":
            emb, entity_map = self.generate_node2vec_graph_embeddings(base_name)
        elif embedding_method == "transe" or embedding_method == "rotate":
            emb, entity_map = self.generate_grape_graph_embeddings(base_name,embedding_method)

        return emb,entity_map

        
