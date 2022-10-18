#Creates labels for all new properties that are added to the KG. Output is the new NodeLabels txt file, as well as a dataframe of the new properties and their hash. 

import numpy
import pandas as pd
import argparse

#Define arguments for each required and optional input
def defineArguments():
    parser=argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("--triples-file",dest="TriplesFile",required=False,help="TriplesFile")
    parser.add_argument("--pkl-labels-file",dest="PklLabelsFile",required=False,help="PklLabelsFile")
    parser.add_argument("--gutmgene-labels-types-file",dest="GutMGeneLabelsFile",required=False,help="GutMGeneLabelsFile")
    parser.add_argument("--gutmgene-new-properties-file",dest="GutMGeneNewPropertiesFile",required=False,help="GutMGeneNewPropertiesFile")
    parser.add_argument("--output-dir",dest="OutputDir",required=True,help="OutputDir")


    return parser

###Read in all files
def process_files(triples_file,pkl_labels_file,gutmgene_labels_file,gutmgene_new_properties_file):
    
    #####Load input data
    with open(triples_file, 'r') as f_in:
        triples = set(tuple(x.split('\t')) for x in f_in.read().splitlines())
    f_in.close()

    triples_list = list(triples)

    labels = {}

    with open(pkl_labels_file) as f_in:
        #Skip first line which is column headers
        next(f_in)
        for line in f_in:
            vals = line.strip().split("\t")
            try:
                key, value = vals[2:4]
                labels[key] = value
            except: pass
    
    uri_labels = pd.read_csv(gutmgene_labels_file,sep=',')

    new_properties = pd.read_csv(gutmgene_new_properties_file,sep=',')

    return triples_list,uri_labels,labels,new_properties

def generate_contextual_labels(triples_list,uri_labels,labels,new_properties):

    #Create dict of all PKL hashes and their labels according to the microbe they represent
    microbes_contextual = pd.DataFrame(columns = ['Identifier','Label'])

    for i in range(len(triples_list)):
        s = triples_list[i][0]
        p = triples_list[i][1]
        #Based on patterns added from OWL-NETS, contextual microbe with PKL hash is always a subclass of NCBITaxon, so NCBITaxon will be the object
        o = triples_list[i][2]
        try:
            o_type = uri_labels.loc[uri_labels['Identifier'] == o,'Type'].values[0]
        except: 
            continue

        #Only find relevant contextual microbes, which are PKL hashes, and label those pkl hashes as the contextual microbe
        if o_type == 'microbe' and 'pkt/' in s and '#subClassOf' in p:
            d = {}
            microbe_label = uri_labels.loc[uri_labels['Identifier'] == o,'Label'].values[0]
            d['Identifier'] = s
            d['Label'] = 'CONTEXTUAL ' + microbe_label
            microbes_contextual = microbes_contextual.append(d,ignore_index=True)

    #Get contextual entities in another loop
    #STEP 1: Add UBERON context
    for i in range(len(triples_list)):
        s = triples_list[i][0]
        p = triples_list[i][1]
        o = triples_list[i][2]
        #Based on patterns added from OWL-NETS, location of microbe for context will be UBERON or NCBITaxon with located in as relationship
        if 'pkt/' in s and p == '<http://purl.obolibrary.org/obo/RO_0001025>' and 'UBERON' in o:
            #try:
            microbe_label = microbes_contextual.loc[microbes_contextual['Identifier'] == s,'Label'].iloc[0]
            #except IndexError:
            #print(microbe_label)
            contextual_label = microbe_label + ": " + labels[o]
            #Update microbes_contextual df
            microbes_contextual.loc[microbes_contextual['Identifier'] == s,'Label'] = contextual_label

    #Need to change the mouse label since it is in another language
    labels['<http://purl.obolibrary.org/obo/NCBITaxon_10090>'] = 'Mus musculus'

    #STEP 2: Add organism context
    for i in range(len(triples_list)):
        s = triples_list[i][0]
        p = triples_list[i][1]
        o = triples_list[i][2]
        #Based on patterns added from OWL-NETS, location of microbe for context will be UBERON or NCBITaxon with located in as relationship
        if p == '<http://purl.obolibrary.org/obo/RO_0001025>' and 'NCBITaxon' in o:
            microbe_label = microbes_contextual.loc[microbes_contextual['Identifier'] == s,'Label'].iloc[0]
            contextual_label = microbe_label + " " + labels[o]
            #Update microbes_contextual df
            microbes_contextual.loc[microbes_contextual['Identifier'] == s,'Label'] = contextual_label

    #Add new relationship labels
    for i in range(len(new_properties)):
        d['Identifier'] = '<' + new_properties.iloc[i].loc['Identifier'] + '>'
        d['Label'] = new_properties.iloc[i].loc['Label']
        microbes_contextual = microbes_contextual.append(d,ignore_index=True)

    return microbes_contextual

def output_labels_file(microbes_contextual,output_dir):

    microbes_contextual.to_csv(output_dir + '/gutMGene_microbes_contextual_labels.csv', index = False)

def combine_labels_files(microbes_contextual,uri_labels,output_dir):

    for i in range(len(microbes_contextual)):
        d = {}
        d['Identifier'] = microbes_contextual.iloc[i].loc['Identifier']
        d['CURIE'] = 'none'
        d['Label'] = microbes_contextual.iloc[i].loc['Label']
        d['Type'] = 'microbe'
        uri_labels = uri_labels.append(d,ignore_index=True)

    uri_labels.to_csv(output_dir + '/LabelTypes_gutMGene_URI_LABEL_MAP_contextual.csv', index = False)

    return uri_labels

def combine_pkl_labels(uri_labels,labels):

    for i in range(len(uri_labels)):
        if uri_labels.iloc[i].loc['Identifier'] not in list(labels.values()):
            labels[uri_labels.iloc[i].loc['Identifier']] = uri_labels.iloc[i].loc['Label']

    labels_df = pd.DataFrame(labels.items(), columns=['Identifier', 'Label'])

    return labels_df

######

def main():

    #Generate argument parser and define arguments
    parser = defineArguments()
    args = parser.parse_args()

    #Define Inputs
    triples_file = args.TriplesFile
    #gutMGene_OWLNETS_Triples_Brackets.txt"
    pkl_labels_file = args.PklLabelsFile
    #PheKnowLator_v3.0.2_full_instance_relationsOnly_OWLNETS_NodeLabels.txt 
    gutmgene_labels_file = args.GutMGeneLabelsFile
    #LabelTypes_gutMGene_URI_LABEL_MAP_.csv
    gutmgene_new_properties_file = args.GutMGeneNewPropertiesFile
    #"gutMGene_new_Properties.csv
    output_dir = args.OutputDir
   
    #Algorithm
    triples_list,uri_labels,labels,new_properties = process_files(triples_file,pkl_labels_file,gutmgene_labels_file,gutmgene_new_properties_file)

    microbes_contextual = generate_contextual_labels(triples_list,uri_labels,labels,new_properties)

    output_labels_file(microbes_contextual,output_dir)

    uri_labels = combine_labels_files(microbes_contextual,uri_labels,output_dir)

    labels_new = combine_pkl_labels(uri_labels,labels)

    labels_new.to_csv(output_dir + '/PheKnowLator_v3.0.2_full_instance_relationsOnly_OWLNETS_NodeLabels_NewEntities.txt', sep='\t',index = False)
    
if __name__ == '__main__':
    main()    
