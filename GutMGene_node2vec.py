import os
import argparse

parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
#Extract relationships
parser.add_argument("--triples-integers-file",dest="TriplesIntegersFile",required=True,help="TriplesIntegersFile")

#Generate argument parser and define arguments
args = parser.parse_args()

triples_integers_file = args.TriplesIntegersFile

for j in range(0,1):
    for i in [42]:
        command =  "python GutMGene_sparse_node2vec_wrapper.py --edgelist {} --dim {} --walklen 10 --walknum 20 --window 10"
        os.system(command.format(triples_integers_file,i,))  