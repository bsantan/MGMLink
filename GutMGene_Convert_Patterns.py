#This script will convert identfied patterns from list of relationships and convert them into the specified OWL tuples with the headers "Subject", "Predicate", "Object", without brackets. 

#python GutMGene_Convert_Patterns.py --patterns-csv-file /Users/brooksantangelo/Documents/HunterLab/GutMGene_PKL/Output/gutMGene_OTU_Pattern_Modifications.csv --output-dir ~/Documents/HunterLab/GutMGene_PKL/Output


import argparse
import pandas as pd
import csv
import sys
import os
import hashlib
import argparse

from rdflib import Graph, Namespace, URIRef, BNode, Literal
from rdflib.namespace import RDF,RDFS,OWL
from tqdm import tqdm

parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("--patterns-csv-file",dest="PatternsCsvFile",required=True,help="PatternsCsvFile")
parser.add_argument("--output-dir",dest="OutputDir",required=True,help="OutputDir")

#Generate argument parser and define arguments
args = parser.parse_args()

patterns_csv_file = args.PatternsCsvFile
output_dir = args.OutputDir

orig_triples = pd.read_csv(patterns_csv_file)
orig_triples = orig_triples.dropna(subset=['Pattern'])
orig_triples.fillna('N/A',inplace=True)

#Set namespace attributes
obo = Namespace('http://purl.obolibrary.org/obo/')
pkt = Namespace('http://github.com/callahantiff/PheKnowLator/pkt/')
ncbi = Namespace('http://www.ncbi.nlm.nih.gov/gene/')


pattern=[]

new_relationship_entities = []

for idx,row in orig_triples.iterrows():
    #Always a microbe
    row['S'] =  URIRef(obo + row['S'].strip())
    row['R1'] =  URIRef(obo + row['R1'].strip())
    row['C2'] =  URIRef(obo + row['C2'].strip()) 
    row['C3'] =  URIRef(obo + row['C3'].strip()) 
    row['P'] =  URIRef(obo + row['P'].strip())
    row['E1'] =  URIRef(obo + row['E1'].strip())

    #Classes may be CHEBI or genes, which have no "_"
    row['C1'] =  URIRef(ncbi + row['C1'].strip()) if '_' not in row['C1'] and 'FAKE' not in row['C1'] else URIRef(obo + row['C1'].strip())
    if(row['Pattern'] == 2):
        pattern_string = str(row['S']) + str(row['R1']) + str(row['C2']) + str(row['R1']) + str(row['C3'])
        str_hash = URIRef(pkt + hashlib.md5(pattern_string.encode()).hexdigest())
        #Make sure all genes are integers, no decimal point
        pattern.append((str_hash,str(row['P']),str(row['C1']).replace('.0', '')))
        if str(row['P']) not in sum(new_relationship_entities, []):
            #For inhibitors
            if 'RO_0011016' in str(row['P']):
                new_relationship_entities.append([str(row['P']),'indirectly negatively regulates activity of'])
            #For activators
            if 'RO_0011013' in str(row['P']):
                new_relationship_entities.append([str(row['P']),'indirectly positively regulates activity of'])

        pattern.append((str_hash,RDFS.subClassOf,str(row['S'])))
        pattern.append((str_hash,str(row['R1']),str(row['C2'])))
        pattern.append((str_hash,str(row['R1']),str(row['C3'])))
    if(row['Pattern'] == 3):
        pattern_string1 = str(row['S']) + str(row['R1']) + str(row['C2']) + str(row['R1']) + str(row['C3'])
        pattern_string2 = str(row['P']) + str(row['E1'])
        str_hash1 = URIRef(pkt + hashlib.md5(pattern_string1.encode()).hexdigest())
        str_hash2 = URIRef(pkt + hashlib.md5(pattern_string2.encode()).hexdigest())
        pattern.append((str_hash1,str_hash2,str(row['C1'])))
        pattern.append((str_hash1,RDFS.subClassOf,str(row['S'])))
        pattern.append((str_hash1,str(row['R1']),str(row['C2'])))
        pattern.append((str_hash1,str(row['R1']),str(row['C3'])))
        if str_hash2 not in sum(new_relationship_entities, []):
            #For substrates
            if 'RO_0002429' in str(row['P']):
                new_relationship_entities.append([str_hash2,'PROPERTY metabolizes'])
            #For products
            if 'BFO_0000067' in str(row['P']):
                new_relationship_entities.append([str_hash2,'PROPERTY produces'])
    if(row['Pattern'] == 1):
        pattern.append((str(row['S']),str(row['P']),str(row['C1'])))
    if(row['Pattern'] == 4):
        pattern_string1 = str(row['P']) + str(row['E1'])
        str_hash1 = URIRef(pkt + hashlib.md5(pattern_string1.encode()).hexdigest())
        pattern.append((str(row['S']),str_hash1,str(row['C1'])))

pattern = list(set(pattern))
with open(output_dir + '/gutMGene_OWLNETS_Triples.csv', 'w',newline='') as triples_file:
    writer = csv.writer(triples_file,delimiter=',')
    writer.writerow(["Subject","Predicate","Object"])
    writer.writerows(pattern)

new_relationship_entities_df = pd.DataFrame(new_relationship_entities, columns = ['Identifier','Label'])

new_relationship_entities_df.to_csv(output_dir + '/gutMGene_new_Properties.csv',sep=',',index=False)

