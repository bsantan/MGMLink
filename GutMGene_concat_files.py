#This script will take bracketed tuples as inputs and concatenate them into a new list of tuples. Headers must be "Subjet", "Predicate", "Object"

import pandas as pd
import csv
import sys
import os
import argparse

parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
#Extract relationships
parser.add_argument("--file1",dest="file1",required=True,help="file1")
parser.add_argument("--file2",dest="file2",required=True,help="file2")
parser.add_argument("--file3",dest="file3",required=False,help="file3")
parser.add_argument("--output-dir",dest="OutputDir",required=True,help="OutputDir")

#Generate argument parser and define arguments
args = parser.parse_args()

file1 = args.file1
file2 = args.file2
output_dir = args.OutputDir

if args.file3:
    file3 = args.file3
    #For adding to PKL_v3
    filenames = [file1,file2,file3]
else:
    filenames = [file1,file2]

#For PKL_v3
new_filename = "/PheKnowLator_v3.0.2_full_instance_relationsOnly_OWLNETS_Triples_Identifiers_withGutMGene_withMicrobes.txt"
#new_filename = "/OWLNETS_Triples_Identifiers_GutMGene_Microbes.txt"

# Create a set to store written lines
written_lines = set()
with open(output_dir + new_filename,"w") as outfile:
    #File1 
    with open(filenames[0]) as f1:
        for line in f1:        #keep the header from file1
            if line not in written_lines:
                outfile.write(line)
                written_lines.add(line)

    #File 2 and on
    for x in filenames[1:]:
        with open(x) as f1:
            for line in f1:
                # Don't include header, remove duplicates
                if not line.lower().startswith("subject") and line not in written_lines:
                    outfile.write(line)
                    written_lines.add(line)

