####This script will take in txt files downloaded from the GutMGene db and produce gutMGene_URI_LABEL_MAP as a csv file.

import argparse
import os
import pandas as pd
import csv


#Define arguments for each required and optional input
def defineArguments():
    parser=argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("--gutmgene-microbes-metabs-human",dest="GutMGeneMicrobesMetabsHuman",required=True,help="GutMGeneMicrobesMetabsHuman")

    parser.add_argument("--gutmgene-microbes-metabs-mouse",dest="GutMGeneMicrobesMetabsMouse",required=True,help="GutMGeneMicrobesMetabsMouse")

    parser.add_argument("--gutmgene-microbes-genes-human",dest="GutMGeneMicrobesGenesHuman",required=True,help="GutMGeneMicrobesGenesHuman")

    parser.add_argument("--gutmgene-microbes-genes-mouse",dest="GutMGeneMicrobesGenesMouse",required=True,help="GutMGeneMicrobesGenesMouse")

    parser.add_argument("--manual-microbes-relationships",dest="ManualMicrobesRelationships",required=True,help="ManualMicrobesRelationships")

    parser.add_argument("--output-dir",dest="OutputDir",required=True,help="OutputDir")

    return parser

###Read in all files
def process_gutmgene_db_file(filepath,column_names,db_type):
    #####Load input data
    df = pd.read_csv(filepath,sep='\t')
    #Remove whitespace from column names
    df.columns = df.columns.str.replace(' ','')
    df = df[column_names]
    df = df.replace('  ', ' ',regex=True)
    df['GutMicrobiataNCBIID'] = df['GutMicrobiataNCBIID'].astype('Int64')
    
    #For genes only
    try:
        df['GeneID'] = df['GeneID'].astype('Int64')
    except KeyError:
        pass
    

    #Replace with none for all dfs
    df = df.astype(str)
    df = df.replace('nan', 'none')
    df = df.replace('<NA>', 'none')

    df['GutMicrobiota'] = df['GutMicrobiota'].str.strip()
    #Only applies to metab dbs
    if db_type == 'metab_microbe_h' or db_type == 'metab_microbe_m':
        df["Substrate"] = df["Substrate"].str.lower()
        df["Metabolite"] = df["Metabolite"].str.lower()
        df['SubstrateChEBIID'] = df['SubstrateChEBIID'].str.replace(':','_')
        df['MetaboliteChEBIID'] = df['MetaboliteChEBIID'].str.replace(':','_')

    df = udpate_gutmgene_microbes(df,db_type)

    return df

def udpate_gutmgene_microbes(df,db_type):

    #Specifically change names in metab_microbe human dataset
    if db_type == 'metab_microbe_h':       

        #Flavonifractor plautii ATCC 49531 is used where the GutMicrobiotaNCBIID needs to be 'none'
        df.loc[df['GutMicrobiota'] == 'Bacteroides distasonis','GutMicrobiota'] = 'parabacteroides distasonis'
        df.loc[df['GutMicrobiota'] == 'Anaerobutyricum hallii','GutMicrobiota'] = 'eubacterium hallii'
        df.loc[df['GutMicrobiota'] == 'Clostridium cadaveris CC40 001C','GutMicrobiataNCBIID'] = str(1073355)
        df.loc[df['GutMicrobiota'] == 'Bacillus sp.46','GutMicrobiota'] = 'Bacillus sp. 46'
        df.loc[df['GutMicrobiota'] == 'Clostridium scindens ATCC35704','GutMicrobiota'] = 'Clostridium scindens ATCC 35704'
        df.loc[df['GutMicrobiota'] == 'Clostridium sp. SDG-Mt85-3Db','GutMicrobiataNCBIID'] = df.loc[df['GutMicrobiota'] == 'Flavonifractor plautii ATCC 49531','GutMicrobiataNCBIID']
        df.loc[df['GutMicrobiota'] == 'Bacteroides fragilis SDG-Mt85-5B','GutMicrobiataNCBIID'] = df.loc[df['GutMicrobiota'] == 'Flavonifractor plautii ATCC 49531','GutMicrobiataNCBIID']
        df.loc[df['GutMicrobiota'] == 'Bacteroides fragilis SDG-Mt85-4C','GutMicrobiataNCBIID'] = df.loc[df['GutMicrobiota'] == 'Flavonifractor plautii ATCC 49531','GutMicrobiataNCBIID']
        df.loc[df['GutMicrobiota'] == 'Bacteroides fragilis DIfE-05','GutMicrobiataNCBIID'] = df.loc[df['GutMicrobiota'] == 'Flavonifractor plautii ATCC 49531','GutMicrobiataNCBIID']
        df.loc[df['GutMicrobiota'] == 'Parabacteroides distasonis DSM 20701T','GutMicrobiataNCBIID'] = df.loc[df['GutMicrobiota'] == 'Flavonifractor plautii ATCC 49531','GutMicrobiataNCBIID']
        df.loc[df['GutMicrobiota'] == 'Bacteroides ovatus SDG-Mt85-3C','GutMicrobiataNCBIID'] = df.loc[df['GutMicrobiota'] == 'Flavonifractor plautii ATCC 49531','GutMicrobiataNCBIID']
        df.loc[df['GutMicrobiota'] == 'Eggerthella lenta SECO-Mt75m3','GutMicrobiataNCBIID'] = df.loc[df['GutMicrobiota'] == 'Flavonifractor plautii ATCC 49531','GutMicrobiataNCBIID']
        df.loc[df['GutMicrobiota'] == 'Blautia producta SNU-Julong 732','GutMicrobiataNCBIID'] = df.loc[df['GutMicrobiota'] == 'Flavonifractor plautii ATCC 49531','GutMicrobiataNCBIID']
        df.loc[df['GutMicrobiota'] == 'Enterococcus faecium EPI1','GutMicrobiataNCBIID'] = df.loc[df['GutMicrobiota'] == 'Flavonifractor plautii ATCC 49531','GutMicrobiataNCBIID']
        df.loc[df['GutMicrobiota'] == 'Lactobacillus mucosae EPI2','GutMicrobiataNCBIID'] = df.loc[df['GutMicrobiota'] == 'Flavonifractor plautii ATCC 49531','GutMicrobiataNCBIID']
        df.loc[df['GutMicrobiota'] == 'Finegoldia magna EPI3','GutMicrobiataNCBIID'] = df.loc[df['GutMicrobiota'] == 'Flavonifractor plautii ATCC 49531','GutMicrobiataNCBIID']
        df.loc[df['GutMicrobiota'] == 'Blautia producta SNU-Julong 732','GutMicrobiataNCBIID'] = df.loc[df['GutMicrobiota'] == 'Flavonifractor plautii ATCC 49531','GutMicrobiataNCBIID']
        df.loc[df['GutMicrobiota'] == 'Clostridium scindens VPI 12708','GutMicrobiataNCBIID'] = df.loc[df['GutMicrobiota'] == 'Flavonifractor plautii ATCC 49531','GutMicrobiataNCBIID']
        df.loc[df['GutMicrobiota'] == 'Clostridium butyricum ATCC 19398','GutMicrobiataNCBIID'] = df.loc[df['GutMicrobiota'] == 'Flavonifractor plautii ATCC 49531','GutMicrobiataNCBIID']
        df.loc[df['GutMicrobiota'] == 'Lactobacillus Plantarum','GutMicrobiota'] = 'lactiplantibacillus plantarum'
        df.loc[df['GutMicrobiota'] == 'Lactobacillus paracasei','GutMicrobiota'] = 'lacticaseibacillus paracasei'
        df.loc[df['GutMicrobiota'] == 'Lactobacillus casei Shirota','GutMicrobiota'] = 'lactobacillus casei shirota'
        df.loc[df['GutMicrobiota'] == 'Collinsella tanakaei YIT YIT 12064','GutMicrobiota'] = 'collinsella tanakaei'
        df.loc[df['GutMicrobiota'] == 'Lactobacillus mucosae','GutMicrobiota'] = 'limosilactobacillus mucosae'

    #Specifically change names in metab_microbe mouse dataset
    if db_type == 'metab_microbe_m':    
        df.loc[df['GutMicrobiota'] == 'Bififidobacterium thetaiotaomicron DSM 2079','GutMicrobiataNCBIID'] = df.loc[df['GutMicrobiota'] == 'Flavonifractor plautii ATCC 49531','GutMicrobiataNCBIID']
        df.loc[df['GutMicrobiota'] == 'Clostridium orbiscindens','GutMicrobiota'] = 'flavonifractor plautii'
        df.loc[df['GutMicrobiota'] == 'lactobacilli','GutMicrobiota'] = 'lactobacillus'
        df.loc[df['GutMicrobiota'] == 'Limosilactobacillus reuteri','GutMicrobiota'] = 'lactobacillus reuteri'
        df.loc[df['GutMicrobiota'] == 'Anaerobutyricum hallii','GutMicrobiota'] = 'eubacterium hallii'
        df.loc[df['GutMicrobiota'] == 'Lactobacillus Plantarum','GutMicrobiota'] = 'lactiplantibacillus plantarum'
        df.loc[df['GutMicrobiota'] == 'Lactobacillus plantarum','GutMicrobiota'] = 'lactiplantibacillus plantarum'
        df.loc[df['GutMicrobiota'] == 'Lactobacillus casei Shirota','GutMicrobiota'] = 'lactobacillus casei shirota'
        df.loc[df['GutMicrobiataNCBIID'] == str(200643),'GutMicrobiataNCBIID'] = str(976)

    #Specifically change names in gene_microbe human dataset
    if db_type == 'gene_microbe_h':   
        df.loc[df['GutMicrobiota'] == 'Lactobacillus paracasei','GutMicrobiota'] = 'lacticaseibacillus paracasei'
        df.loc[df['GutMicrobiota'] == 'Faecalibacterium prausnitzii A2–165','GutMicrobiota'] = 'faecalibacterium prausnitzii a2-165'
        df.loc[df['GutMicrobiota'] == 'Bacteroides vulgatus','GutMicrobiota'] = 'phocaeicola vulgatus'
        df.loc[df['GutMicrobiota'] == 'Bacteroides distasonis','GutMicrobiota'] = 'parabacteroides distasonis'
        df.loc[df['GutMicrobiota'] == 'Lactobacillus Plantarum','GutMicrobiota'] = 'lactiplantibacillus plantarum'
        df.loc[df['GutMicrobiota'] == 'Lactobacillus plantarum','GutMicrobiota'] = 'lactiplantibacillus plantarum'
        df.loc[df['GutMicrobiota'] == 'Escherichia coli E2348/69','GutMicrobiota'] = 'escherichia coli o127:h6 str. e2348/69'
        df.loc[df['GutMicrobiota'] == 'Lactobacillus casei Shirota','GutMicrobiota'] = 'lactobacillus casei shirota'
        df.loc[df['GutMicrobiota'] == 'Lactobacillus casei shirota','GutMicrobiota'] = 'lactobacillus casei shirota'

    #Specifically change names in gene_microbe mouse dataset
    if db_type == 'gene_microbe_m':   
        df.loc[df['GutMicrobiota'] == 'Anaerobutyricum hallii','GutMicrobiota'] = 'eubacterium hallii'
        df.loc[df['GutMicrobiota'] == 'Lactobacillus plantarum','GutMicrobiota'] = 'lactiplantibacillus plantarum'
        df.loc[df['GutMicrobiota'] == 'lactobacilli','GutMicrobiota'] = 'lactobacillus'
        df.loc[df['GutMicrobiota'] == 'Lactobacillus paracasei','GutMicrobiota'] = 'lacticaseibacillus paracasei'
        df.loc[df['GutMicrobiota'] == 'Lactobacillus casei Shirota','GutMicrobiota'] = 'lactobacillus casei shirota'
        df.loc[df['GutMicrobiota'] == 'Lactobacillus casei shirota','GutMicrobiota'] = 'lactobacillus casei shirota'
        for i in range(len(df)):
            if df.iloc[i].loc['Gene'] == 'Il12p70':
                d = {}
                d['GutMicrobiota'] = df.iloc[i].loc['GutMicrobiota']
                d['GutMicrobiataNCBIID'] = df.iloc[i].loc['GutMicrobiataNCBIID']
                d['Gene'] = 'IL12B'
                d['GeneID'] = str(3593)
                d['Alteration'] = df.iloc[i].loc['Alteration']
                df = pd.concat([df, pd.DataFrame([d])], ignore_index=True)
        df.loc[df['Gene'] == 'Il12p70','GeneID'] = str(3592)
        df.loc[df['Gene'] == 'Il12p70','Gene'] = 'IL12A'

    df['GutMicrobiota'] = df['GutMicrobiota'].str.strip()

    #Add NCBITaxon_ to all Microbe IDs for CURIE
    df = df.astype(str)
    df = df.replace('nan', 'none')
    for i in range(len(df)):
        if str(df.iloc[i].loc['GutMicrobiataNCBIID']) != 'none':
            df.loc[i,'GutMicrobiataNCBIID'] = 'NCBITaxon_' + str(int(df.iloc[i].loc['GutMicrobiataNCBIID']))

    return df

def combine_gutMGene_manual_microbes(gutmgene_all,manual_microbes_file):

    manual_microbes = pd.read_csv(manual_microbes_file,sep=',')
    manual_microbes = manual_microbes.astype(str)
    manual_microbes = manual_microbes.replace('nan', 'none')
    manual_microbes['GutMicrobiota'] = [str(i).lower() for i in manual_microbes['GutMicrobiota']]
    manual_microbes['Taxa'] = [str(i).lower() for i in manual_microbes['Taxa']]
    manual_microbes['Relationship'] = 'http://www.w3.org/2000/01/rdf-schema#subClassOf'

    #New df for all relevant microbes in gutMGene to include the manual relationships
    gutMgene_microbes_updated = pd.DataFrame(columns=['GutMicrobiota','GutMicrobiataNCBIID','Relationship','Taxa','TaxaNCBIID'])
    
    for i in range(len(gutmgene_all)):
        d = {}
        d['GutMicrobiota'] = gutmgene_all.loc[i,'GutMicrobiota']
        d['GutMicrobiataNCBIID'] = gutmgene_all.loc[i,'GutMicrobiataNCBIID']
        if d['GutMicrobiota'].lower() in list(manual_microbes['GutMicrobiota']):
            d['Relationship'] = 'http://www.w3.org/2000/01/rdf-schema#subClassOf'
            d['Taxa'] = manual_microbes.loc[manual_microbes['GutMicrobiota'] == d['GutMicrobiota'].lower(),'Taxa'].values[0]
            d['TaxaNCBIID'] = manual_microbes.loc[manual_microbes['GutMicrobiota'] == d['GutMicrobiota'].lower(),'TaxaNCBIID'].values[0]
        else:
            d['Relationship'] = 'none'
            d['Taxa'] = 'none'
            d['TaxaNCBIID'] = 'none'
        gutMgene_microbes_updated = pd.concat([gutMgene_microbes_updated, pd.DataFrame([d])], ignore_index=True)

    gutMgene_microbes_updated = gutMgene_microbes_updated[['GutMicrobiota','GutMicrobiataNCBIID','Relationship','Taxa','TaxaNCBIID']]
    gutMgene_microbes_updated = gutMgene_microbes_updated.drop_duplicates(subset=['GutMicrobiota'])
    gutMgene_microbes_updated = gutMgene_microbes_updated.reset_index(drop=True)

    return gutMgene_microbes_updated

def create_uri_label_map(gutMGene_values,df,db_type,fake_id_dataset,fake_id_count):

    df = df.astype(str)
    df = df.replace('nan', 'none')

    if db_type == 'microbes':
        #Add new microbes with an ID
        for i in range(len(df)):
            d = {}
            identifier = 'http://purl.obolibrary.org/obo/'+str(df.iloc[i].loc["GutMicrobiataNCBIID"])
            if identifier not in gutMGene_values.values and df.iloc[i].loc["GutMicrobiataNCBIID"] != 'none':
                d['Identifier'] = identifier
                d['CURIE'] = df.iloc[i].loc["GutMicrobiataNCBIID"]
                d['Label'] = df.iloc[i].loc["GutMicrobiota"]
                d['Type'] = 'microbe'
                gutMGene_values = pd.concat([gutMGene_values, pd.DataFrame([d])], ignore_index=True)
            
            d = {}
            taxa_identifier = 'http://purl.obolibrary.org/obo/'+str(df.iloc[i].loc["TaxaNCBIID"])
            if taxa_identifier not in gutMGene_values.values and df.iloc[i].loc["TaxaNCBIID"] != 'none':
                d['Identifier'] = taxa_identifier
                d['CURIE'] = df.iloc[i].loc["TaxaNCBIID"]
                d['Label'] = df.iloc[i].loc["Taxa"]
                d['Type'] = 'microbe'
                gutMGene_values = pd.concat([gutMGene_values, pd.DataFrame([d])], ignore_index=True)

            #Add microbes without an ID
            if df.iloc[i].loc['GutMicrobiataNCBIID'] == 'none' and df.iloc[i].loc['GutMicrobiota'] != 'none':
                d = {}
                fake_id = f'{fake_id_count:07d}'
                d['Identifier'] = 'http://purl.obolibrary.org/obo/' + 'FAKEURI_' + fake_id
                d['CURIE'] = 'FAKEURI_' + fake_id
                d['Label'] = df.iloc[i].loc['GutMicrobiota']
                d['Type'] = 'microbe'
                fake_id_dataset = pd.concat([fake_id_dataset, pd.DataFrame([d])], ignore_index=True)
                fake_id_count += 1

    if 'metab' in db_type:

        #Add substrates and metabs with an ID
        for i in range(len(df)):
            if df.iloc[i].loc['SubstrateChEBIID'] != 'none' and df.iloc[i].loc['Substrate'] != 'none':
                d = {}
                identifier = 'http://purl.obolibrary.org/obo/' + df.iloc[i].loc['SubstrateChEBIID']
                if identifier not in gutMGene_values.values:
                    if df.iloc[i].loc['SubstrateChEBIID'] != 'none' and df.iloc[i].loc['Substrate'] != 'none':
                        d['Identifier'] = 'http://purl.obolibrary.org/obo/' + df.iloc[i].loc['SubstrateChEBIID']
                        d['CURIE'] = df.iloc[i].loc['SubstrateChEBIID']
                        d['Label'] = df.iloc[i].loc['Substrate']
                        d['Type'] = 'other'
                        gutMGene_values = pd.concat([gutMGene_values, pd.DataFrame([d])], ignore_index=True)
            if df.iloc[i].loc['MetaboliteChEBIID'] != 'none' and df.iloc[i].loc['Metabolite'] != 'none':
                d = {}
                identifier = 'http://purl.obolibrary.org/obo/' + df.iloc[i].loc['MetaboliteChEBIID']  
                if identifier not in gutMGene_values.values:
                    if df.iloc[i].loc['MetaboliteChEBIID'] != 'none' and df.iloc[i].loc['Metabolite'] != 'none':
                        d = {}
                        d['Identifier'] = 'http://purl.obolibrary.org/obo/' + df.iloc[i].loc['MetaboliteChEBIID']
                        d['CURIE'] = df.iloc[i].loc['MetaboliteChEBIID']
                        d['Label'] = df.iloc[i].loc['Metabolite']
                        d['Type'] = 'other'
                        gutMGene_values = pd.concat([gutMGene_values, pd.DataFrame([d])], ignore_index=True)

        #Add substrates and metabs without an ID
            if df.iloc[i].loc['SubstrateChEBIID'] == 'none' and df.iloc[i].loc['Substrate'] != 'none':
                d = {}
                fake_id = f'{fake_id_count:07d}'
                d['Identifier'] = 'http://purl.obolibrary.org/obo/' + 'FAKEURI_' + fake_id
                d['CURIE'] = 'FAKEURI_' + fake_id
                d['Label'] = df.iloc[i].loc['Substrate']
                d['Type'] = 'other'
                if d['Label'].lower() not in list(map(str.lower, fake_id_dataset['Label'].values)):
                    fake_id_dataset = pd.concat([fake_id_dataset, pd.DataFrame([d])], ignore_index=True)
                    fake_id_count += 1
            if df.iloc[i].loc['MetaboliteChEBIID'] == 'none' and df.iloc[i].loc['Metabolite'] != 'none':
                d = {}
                fake_id = f'{fake_id_count:07d}'
                d['Identifier'] = 'http://purl.obolibrary.org/obo/' + 'FAKEURI_' + fake_id
                d['CURIE'] = 'FAKEURI_' + fake_id
                d['Label'] = df.iloc[i].loc['Metabolite']
                d['Type'] = 'other'
                if d['Label'].lower() not in list(map(str.lower, fake_id_dataset['Label'].values)):
                    fake_id_dataset = pd.concat([fake_id_dataset, pd.DataFrame([d])], ignore_index=True)
                    fake_id_count += 1

    if 'gene' in db_type:
        for i in range(len(df)):
            #Add genes with an ID
            if df.iloc[i].loc['GeneID'] != 'none' and df.iloc[i].loc['Gene'] != 'none':
                d = {}
                identifier = 'http://www.ncbi.nlm.nih.gov/gene/'+str(df.iloc[i].loc["GeneID"])
                if identifier not in gutMGene_values.values:
                    d['Identifier'] = identifier
                    d['CURIE'] = df.iloc[i].loc["GeneID"]
                    d['Label'] = df.iloc[i].loc["Gene"]
                    d['Type'] = 'other'
                    gutMGene_values = pd.concat([gutMGene_values, pd.DataFrame([d])], ignore_index=True)

            #Add genes without an ID
            if df.iloc[i].loc['GeneID'] == 'none' and df.iloc[i].loc['Gene'] != 'none':
                d = {}
                fake_id = f'{fake_id_count:07d}'
                d['Identifier'] = 'http://purl.obolibrary.org/obo/' + 'FAKEURI_' + fake_id
                d['CURIE'] = 'FAKEURI_' + fake_id
                d['Label'] = df.iloc[i].loc['Gene']
                d['Type'] = 'other'
                if d['Label'].lower() not in list(map(str.lower, fake_id_dataset['Label'].values)):
                    fake_id_dataset = pd.concat([fake_id_dataset, pd.DataFrame([d])], ignore_index=True)
                    fake_id_count += 1
    

    #Remove any rows that are none for identifier, curie, and label
    gutMGene_values = gutMGene_values.astype(str)
    gutMGene_values = gutMGene_values.replace('nan', 'none')
    gutMGene_values.drop(gutMGene_values.loc[gutMGene_values['Label']=='none'].index, inplace=True)

    return gutMGene_values,fake_id_dataset,fake_id_count

#To create gutMGene_URI_LABEL_MAP
def concatenate_uri_labels(gutMGene_values,updated_fake_IDs):

    updated_fake_IDs["Identifier"] = '<'+updated_fake_IDs["Identifier"]+'>'

    gutMGene_values["Identifier"] = '<'+gutMGene_values["Identifier"]+'>'

    gutMGene_IDs = pd.concat([gutMGene_values,updated_fake_IDs],axis=0)
    gutMGene_IDs = gutMGene_IDs.drop_duplicates(subset=['Identifier'])
    gutMGene_IDs = gutMGene_IDs.reset_index(drop=True)

    gutMGene_IDs['Label'] = gutMGene_IDs['Label'].str.lower()
    gutMGene_IDs['Label'] = gutMGene_IDs['Label'].str.strip()

    return gutMGene_IDs



def create_microbe_triples(gutMGene_all_microbes_updated,gutMGene_IDs):

    gutMGene_all_microbes_updated = gutMGene_all_microbes_updated.astype(str)
    gutMGene_all_microbes_updated = gutMGene_all_microbes_updated.replace('nan', 'none')

    #Create a df with all new triples
    gutmgene_microbes_relationships = pd.DataFrame(columns=['Subject','Predicate','Object'])

    for i in range(len(gutMGene_all_microbes_updated)):
        d = {}
        if gutMGene_all_microbes_updated.iloc[i].loc['GutMicrobiataNCBIID'] != 'none' and gutMGene_all_microbes_updated.iloc[i].loc['Taxa'] != 'none':
            d['Subject'] = 'http://purl.obolibrary.org/obo/' + gutMGene_all_microbes_updated.iloc[i].loc['GutMicrobiataNCBIID']
            d['Predicate'] = gutMGene_all_microbes_updated.iloc[i].loc['Relationship']
            d['Object'] = 'http://purl.obolibrary.org/obo/' + gutMGene_all_microbes_updated.iloc[i].loc['TaxaNCBIID']
            gutmgene_microbes_relationships = pd.concat([gutmgene_microbes_relationships, pd.DataFrame([d])], ignore_index=True)
        d = {}
        if gutMGene_all_microbes_updated.iloc[i].loc['GutMicrobiataNCBIID'] == 'none' and gutMGene_all_microbes_updated.iloc[i].loc['Taxa'] != 'none':
            s = gutMGene_all_microbes_updated.iloc[i].loc['GutMicrobiota'].lower()
            #Get FAKEID
            d['Subject'] = 'http://purl.obolibrary.org/obo/' + gutMGene_IDs.loc[gutMGene_IDs['Label'] == s,'CURIE'].item()
            d['Predicate'] = gutMGene_all_microbes_updated.iloc[i].loc['Relationship']
            d['Object'] = 'http://purl.obolibrary.org/obo/' + gutMGene_all_microbes_updated.iloc[i].loc['TaxaNCBIID']
            gutmgene_microbes_relationships = pd.concat([gutmgene_microbes_relationships, pd.DataFrame([d])], ignore_index=True)

    return gutmgene_microbes_relationships

#For microbes, use gutMgene_microbes_updated above since I manually updated those names and IDs. For Chebi IDs, use what was given in gutMGene
def generate_patterns(gutMGene_patterns,gutMGene_IDs,df,db_type,count):

    #Make sure these are covered
    df = df.astype(str)
    df = df.replace('nan', 'none')

    if db_type == 'metab_microbe_h':
        for i in range(len(df)):
            #Human
            #Add microbe substrates
            d = {}
            if df.iloc[i].loc['Substrate'] != 'none' and df.iloc[i].loc['GutMicrobiota'] != 'none':
                d['Pattern ID'] = count
                d['Pattern'] = 3
                d['MB Pattern Type'] = 's r1 o r2 c2 (property chain)'
                d['S'] = gutMGene_IDs.loc[gutMGene_IDs['Label'] == df.iloc[i].loc['GutMicrobiota'].lower(),'CURIE'].values[0]
                d['R1'] = 'RO_0001025'
                d['a'] = 'some'
                d['C2'] = 'UBERON_0004907'
                d['b'] = 'and'
                d['c'] = 'some'
                d['C3'] = 'NCBITaxon_9606'
                d['d'] = 'and'
                d['P'] = 'RO_0002429'
                d['e'] = 'o'
                d['E1'] = 'RO_0004007'
                d['C1'] = gutMGene_IDs.loc[gutMGene_IDs['Label'] == df.iloc[i].loc['Substrate'].lower(),'CURIE'].values[0]
                gutMGene_patterns = pd.concat([gutMGene_patterns, pd.DataFrame([d])], ignore_index=True)
                count += 1
            #Add microbe metabolites
            d = {}
            if df.iloc[i].loc['Metabolite'] != 'none' and df.iloc[i].loc['GutMicrobiota'] != 'none':
                d['Pattern ID'] = count
                d['Pattern'] = 3
                d['MB Pattern Type'] = 's r1 o r2 c2 (property chain)'
                d['S'] = gutMGene_IDs.loc[gutMGene_IDs['Label'] == df.iloc[i].loc['GutMicrobiota'].lower(),'CURIE'].values[0]
                d['R1'] = 'RO_0001025'
                d['a'] = 'some'
                d['C2'] = 'UBERON_0004907'
                d['b'] = 'and'
                d['c'] = 'some'
                d['C3'] = 'NCBITaxon_9606'
                d['d'] = 'and'
                d['P'] = 'BFO_0000067'
                d['e'] = 'o'
                d['E1'] = 'RO_0002234'
                d['C1'] = gutMGene_IDs.loc[gutMGene_IDs['Label'] == df.iloc[i].loc['Metabolite'].lower(),'CURIE'].values[0]
                gutMGene_patterns = pd.concat([gutMGene_patterns, pd.DataFrame([d])], ignore_index=True)
                count += 1
      
    if db_type == 'metab_microbe_m':
        for i in range(len(df)):
            #Add microbe substrates
            d = {}
            if df.iloc[i].loc['Substrate'] != 'none' and df.iloc[i].loc['GutMicrobiota'] != 'none':
                d['Pattern ID'] = count
                d['Pattern'] = 3
                d['MB Pattern Type'] = 'c1 and r1 o r2 c2 (property chain)'
                d['S'] = gutMGene_IDs.loc[gutMGene_IDs['Label'] == df.iloc[i].loc['GutMicrobiota'].lower(),'CURIE'].values[0]
                d['R1'] = 'RO_0001025'
                d['a'] = 'some'
                d['C2'] = 'UBERON_0004907'
                d['b'] = 'and'
                d['c'] = 'some'
                d['C3'] = 'NCBITaxon_10090'
                d['d'] = 'and'
                d['P'] = 'BFO_0000067'
                d['e'] = 'o'
                d['E1'] = 'RO_0002234'
                d['C1'] = gutMGene_IDs.loc[gutMGene_IDs['Label'] == df.iloc[i].loc['Substrate'].lower(),'CURIE'].values[0]
                gutMGene_patterns = pd.concat([gutMGene_patterns, pd.DataFrame([d])], ignore_index=True)
                count += 1
            #Add microbe metabolites
            d = {}
            if df.iloc[i].loc['Metabolite'] != 'none' and df.iloc[i].loc['GutMicrobiota'] != 'none':
                d['Pattern ID'] = count
                d['Pattern'] = 3
                d['MB Pattern Type'] = 'c1 and r1 o r2 c2 (property chain)'  
                d['S'] = gutMGene_IDs.loc[gutMGene_IDs['Label'] == df.iloc[i].loc['GutMicrobiota'].lower(),'CURIE'].values[0]
                d['R1'] = 'RO_0001025'
                d['a'] = 'some'
                d['C2'] = 'UBERON_0004907'
                d['b'] = 'and'
                d['c'] = 'some'
                d['C3'] = 'NCBITaxon_10090'
                d['d'] = 'and'
                d['P'] = 'BFO_0000067'
                d['e'] = 'o'
                d['E1'] = 'RO_0002234'
                d['C1'] = gutMGene_IDs.loc[gutMGene_IDs['Label'] == df.iloc[i].loc['Metabolite'].lower(),'CURIE'].values[0]
                gutMGene_patterns = pd.concat([gutMGene_patterns, pd.DataFrame([d])], ignore_index=True)
                count += 1

    if db_type == 'gene_microbe_h':
        for i in range(len(df)):   
            #Add microbe activation genes
            #Use gene names from GutMGene since there are identical names for different IDs
            d = {}
            if df.iloc[i].loc['Alteration'] == 'activation' and df.iloc[i].loc['GutMicrobiota'] != 'none':
                d['Pattern ID'] = count
                d['Pattern'] = 2
                d['MB Pattern Type'] = 'c1 and r c2 (basic triple 2)'
                d['S'] = gutMGene_IDs.loc[gutMGene_IDs['Label'] == df.iloc[i].loc['GutMicrobiota'].lower(),'CURIE'].values[0]
                d['R1'] = 'RO_0001025'
                d['a'] = 'some'
                d['C2'] = 'UBERON_0004907'
                d['b'] = 'and'
                d['c'] = 'some'
                d['C3'] = 'NCBITaxon_9606'
                d['d'] = 'and'
                d['P'] = 'RO_0011013'
                d['e'] = ''
                d['E1'] = ''
                d['C1'] = str(df.iloc[i].loc['GeneID'])
                gutMGene_patterns = pd.concat([gutMGene_patterns, pd.DataFrame([d])], ignore_index=True)
                count += 1
            #Add microbe inhibition genes
            d = {}
            #if gutMGene_gene_microbe.iloc[i].loc['Alteration'] == 'inhibition' and gutMGene_gene_microbe.iloc[i].loc['GutMicrobiataNCBIID'] != 'none':
            if df.iloc[i].loc['Alteration'] == 'inhibition' and df.iloc[i].loc['GutMicrobiota'] != 'none':
                d['Pattern ID'] = count
                d['Pattern'] = 2
                d['MB Pattern Type'] = 'c1 and r c2 (basic triple 2)'
                d['S'] = gutMGene_IDs.loc[gutMGene_IDs['Label'] == df.iloc[i].loc['GutMicrobiota'].lower(),'CURIE'].values[0]
                d['R1'] = 'RO_0001025'
                d['a'] = 'some'
                d['C2'] = 'UBERON_0004907'
                d['b'] = 'and'
                d['R1'] = 'RO_0001025'
                d['c'] = 'some'
                d['C3'] = 'NCBITaxon_9606'
                d['d'] = 'and'
                d['P'] = 'RO_0011016'
                d['e'] = ''
                d['E1'] = ''
                d['C1'] = str(df.iloc[i].loc['GeneID'])
                gutMGene_patterns = pd.concat([gutMGene_patterns, pd.DataFrame([d])], ignore_index=True)
                count += 1

    if db_type == 'gene_microbe_m':
        for i in range(len(df)): 
            #Add microbe activation genes
            d = {}
            if df.iloc[i].loc['Alteration'] == 'activation' and df.iloc[i].loc['GutMicrobiota'] != 'none':
                d['Pattern ID'] = count
                d['Pattern'] = 2
                d['MB Pattern Type'] = 'c1 and r c2 (basic triple 2)'
                d['S'] = gutMGene_IDs.loc[gutMGene_IDs['Label'] == df.iloc[i].loc['GutMicrobiota'].lower(),'CURIE'].values[0]
                d['R1'] = 'RO_0001025'
                d['a'] = 'some'
                d['C2'] = 'UBERON_0004907'
                d['b'] = 'and'
                d['c'] = 'some'
                d['C3'] = 'NCBITaxon_10090'
                d['d'] = 'and'
                d['P'] = 'RO_0011013'
                d['e'] = ''
                d['E1'] = ''
                d['C1'] = str(df.iloc[i].loc['GeneID'])
                gutMGene_patterns = pd.concat([gutMGene_patterns, pd.DataFrame([d])], ignore_index=True)
                count += 1
            #Add microbe inhibition genes
            d = {}
            if df.iloc[i].loc['Alteration'] == 'inhibition' and df.iloc[i].loc['GutMicrobiota'] != 'none':
                d['Pattern ID'] = count
                d['Pattern'] = 2
                d['MB Pattern Type'] = 'c1 and r c2 (basic triple 2)'
                d['S'] = gutMGene_IDs.loc[gutMGene_IDs['Label'] == df.iloc[i].loc['GutMicrobiota'].lower(),'CURIE'].values[0]
                d['R1'] = 'RO_0001025'
                d['a'] = 'some'
                d['C2'] = 'UBERON_0004907'
                d['b'] = 'and'
                d['c'] = 'some'
                d['C3'] = 'NCBITaxon_10090'
                d['d'] = 'and'
                d['P'] = 'RO_0011016'
                d['e'] = ''
                d['E1'] = ''
                d['C1'] = str(df.iloc[i].loc['GeneID'])
                gutMGene_patterns = pd.concat([gutMGene_patterns, pd.DataFrame([d])], ignore_index=True)
                count += 1

    return gutMGene_patterns,count

def process_gutMGene_patterns(gutMGene_patterns):

    #Start Pattern ID at 1 and drop duplicates
    gutMGene_patterns = gutMGene_patterns.drop_duplicates(subset=gutMGene_patterns.columns.difference(['Pattern ID'])).reset_index(drop=True)
    gutMGene_patterns['Pattern ID'] = range(1,len(gutMGene_patterns)+1)

    return gutMGene_patterns

def create_csv_file(df,output_dir,filename,used_columns):
    print("output_dir here:-------")
    print(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    if used_columns == 'all':
        df.to_csv(output_dir+filename,sep=',',index=False)
    else:
        df.to_csv(output_dir+filename,sep=',',index=False,columns = used_columns)

    print(output_dir+filename)

def main():

    #Generate argument parser and define arguments
    parser = defineArguments()
    args = parser.parse_args()
    
    gutMGene_metab_microb_h_file = args.GutMGeneMicrobesMetabsHuman
    gutMGene_metab_microb_m_file = args.GutMGeneMicrobesMetabsMouse
    gutMGene_gene_microb_h_file = args.GutMGeneMicrobesGenesHuman
    gutMGene_gene_microb_m_file = args.GutMGeneMicrobesGenesMouse
    manual_microbes_file = args.ManualMicrobesRelationships
    output_dir = args.OutputDir

    db_dict = {
        'metab_microbe_h':[{'filename':gutMGene_metab_microb_h_file,'columns':list(['GutMicrobiota','GutMicrobiataNCBIID','Substrate','SubstrateChEBIID','Metabolite','MetaboliteChEBIID'])}],
        'metab_microbe_m':[{'filename':gutMGene_metab_microb_m_file,'columns':list(['GutMicrobiota','GutMicrobiataNCBIID','Substrate','SubstrateChEBIID','Metabolite','MetaboliteChEBIID'])}],
        'gene_microbe_h':[{'filename':gutMGene_gene_microb_h_file,'columns':list(['GutMicrobiota','GutMicrobiataNCBIID','Gene','GeneID','Alteration'])}],
        'gene_microbe_m':[{'filename':gutMGene_gene_microb_m_file,'columns':list(['GutMicrobiota','GutMicrobiataNCBIID','Gene','GeneID','Alteration'])}]
    }

    #Human microbe-metabolite db
    gutMGene_metab_microbe_h = process_gutmgene_db_file(db_dict['metab_microbe_h'][0]['filename'],db_dict['metab_microbe_h'][0]['columns'],'metab_microbe_h')

    #Mouse microbe-metabolite db
    gutMGene_metab_microbe_m = process_gutmgene_db_file(db_dict['metab_microbe_m'][0]['filename'],db_dict['metab_microbe_m'][0]['columns'],'metab_microbe_m')
    
    #Human microbe-gene db
    gutMGene_gene_microbe_h = process_gutmgene_db_file(db_dict['gene_microbe_h'][0]['filename'],db_dict['gene_microbe_h'][0]['columns'],'gene_microbe_h')

    #Mouse microbe-gene db
    gutMGene_gene_microbe_m = process_gutmgene_db_file(db_dict['gene_microbe_m'][0]['filename'],db_dict['gene_microbe_m'][0]['columns'],'gene_microbe_m')

    #Concatenate all files only for getting all microbes together
    gutmgene_all = pd.concat([gutMGene_metab_microbe_h,gutMGene_metab_microbe_m,gutMGene_gene_microbe_h,gutMGene_gene_microbe_m], axis=0)
    gutmgene_all = gutmgene_all.reset_index(drop=True)

    gutMGene_all_microbes_updated = combine_gutMGene_manual_microbes(gutmgene_all,manual_microbes_file)

    if 'generate_intermediate_files':
        os.makedirs(output_dir, exist_ok=True)
        create_csv_file(gutMGene_all_microbes_updated,output_dir,'/gutMgene_microbes_updated.csv','all')

    #Entities in gutMGene have ontology identifiers
    gutMGene_values = pd.DataFrame(columns=['Identifier','CURIE','Label','Type'])

    #Entities in gutMGene do not have ontology identifiers
    updated_fake_IDs = pd.DataFrame(columns=['Identifier','CURIE','Label','Type'])
    fake_id_count = 1

    #Microbes
    gutMGene_values,updated_fake_IDs,fake_id_count = create_uri_label_map(gutMGene_values,gutMGene_all_microbes_updated,'microbes',updated_fake_IDs,fake_id_count)

    #Genes
    gutMGene_values,updated_fake_IDs,fake_id_count = create_uri_label_map(gutMGene_values,gutMGene_gene_microbe_h,'gene_microbe_h',updated_fake_IDs,fake_id_count)
    gutMGene_values,updated_fake_IDs,fake_id_count = create_uri_label_map(gutMGene_values,gutMGene_gene_microbe_m,'gene_microbe_m',updated_fake_IDs,fake_id_count)

    #Metabs
    gutMGene_values,updated_fake_IDs,fake_id_count = create_uri_label_map(gutMGene_values,gutMGene_metab_microbe_h,'metab_microbe_h',updated_fake_IDs,fake_id_count)
    gutMGene_values,updated_fake_IDs,fake_id_count = create_uri_label_map(gutMGene_values,gutMGene_metab_microbe_m,'metab_microbe_m',updated_fake_IDs,fake_id_count)

    gutMGene_IDs = concatenate_uri_labels(gutMGene_values,updated_fake_IDs)

    create_csv_file(gutMGene_IDs,output_dir,'/gutMGene_URI_LABEL_MAP.csv',list(['Identifier','CURIE','Label']))

    create_csv_file(gutMGene_IDs,output_dir,'/LabelTypes_gutMGene_URI_LABEL_MAP.csv','all')

    gutmgene_microbes_relationships = create_microbe_triples(gutMGene_all_microbes_updated,gutMGene_IDs)

    create_csv_file(gutmgene_microbes_relationships,output_dir,'/microbes_Triples.csv','all')

    #Create assertions
    count = 1

    #Build the substrate chains
    gutMGene_patterns = pd.DataFrame(columns=['Pattern ID','Pattern','MB Pattern Type','S','R1','a','C2','b','c','C3','d','P','e','E1','C1'])

    #Metabs
    gutMGene_patterns,count = generate_patterns(gutMGene_patterns,gutMGene_IDs,gutMGene_metab_microbe_h,'metab_microbe_h',count)
    gutMGene_patterns,count = generate_patterns(gutMGene_patterns,gutMGene_IDs,gutMGene_metab_microbe_m,'metab_microbe_m',count)
    #Genes
    gutMGene_patterns,count = generate_patterns(gutMGene_patterns,gutMGene_IDs,gutMGene_gene_microbe_h,'gene_microbe_h',count)
    gutMGene_patterns,count = generate_patterns(gutMGene_patterns,gutMGene_IDs,gutMGene_gene_microbe_m,'gene_microbe_m',count)

    gutMGene_patterns = process_gutMGene_patterns(gutMGene_patterns)

    create_csv_file(gutMGene_patterns,output_dir,'/gutMGene_OTU_Pattern_Modifications.csv','all')

if __name__ == '__main__':
    main()
