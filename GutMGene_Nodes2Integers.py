import json
from tqdm import tqdm
import argparse

# read in original data file 

parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
#Extract relationships
parser.add_argument("--triples-input-file",dest="TriplesInputFile",required=True,help="TriplesInputFile")
parser.add_argument("--output-dir",dest="OutputDir",required=True,help="OutputDir")

#Generate argument parser and define arguments
args = parser.parse_args()

triples_input_file = args.TriplesInputFile
output_dir = args.OutputDir

with open(triples_input_file, 'r') as f_in:
    #Length matches original file length
    kg_data = set(tuple(x.split('\t')) for x in f_in.read().splitlines())
f_in.close()

# set output filenames
output_ints_location = output_dir+'/PheKnowLator_v3.0.2_full_instance_relationsOnly_OWLNETS_Triples_Integers_node2vecInput_withGutMGene_withMicrobes.txt'
output_ints_map_location = output_dir+'/PheKnowLator_v3.0.2_full_instance_relationsOnly_OWLNETS_Triples_Integer_Identifier_Map_withGutMGene_withMicrobes.json'


# map identifiers to integers
entity_map = {}
entity_counter = 0
graph_len = len(kg_data)

ints = open(output_ints_location, 'w', encoding='utf-8')
ints.write('subject' + '\t' + 'predicate' + '\t' + 'object' + '\n')

for s, p, o in tqdm(kg_data):
    subj, pred, obj = s, p, o
    if subj not in entity_map: entity_counter += 1; entity_map[subj] = entity_counter
    if pred not in entity_map: entity_counter += 1; entity_map[pred] = entity_counter
    if obj not in entity_map: entity_counter += 1; entity_map[obj] = entity_counter
    ints.write('%d' % entity_map[subj] + '\t' + '%d' % entity_map[pred] + '\t' + '%d' % entity_map[obj] + '\n')
ints.close()

#write out the identifier-integer map
with open(output_ints_map_location, 'w') as file_name:
    json.dump(entity_map, file_name)



# read original data file and convert 3 columns to 2 (just subjects and objects)
inputs_ints_file_loc = output_dir+'/PheKnowLator_v3.0.2_full_instance_relationsOnly_OWLNETS_Triples_Integers_node2vecInput_withGutMGene_withMicrobes.txt'


with open(inputs_ints_file_loc) as f_in:
    kg_data = [x.split('\t')[0::2] for x in f_in.read().splitlines()]
f_in.close()

file_out = output_dir+'/PheKnowLator_v3.0.2_full_instance_relationsOnly_OWLNETS_Triples_node2vecInput_cleaned_withGutMGene_withMicrobes.txt'


with open(file_out, 'w') as f_out:
    for x in kg_data[1:]:
        f_out.write(x[0] + ' ' + x[1] + '\n')

f_out.close()