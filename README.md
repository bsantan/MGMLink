# MGMLink, a Knoweldge Graph of Microbe - Gene - Metabolite Linkages

This MGMLink repository consists of the workflow needed to generate the MGMLink knowledge graph. The KG is generated using a SnakeMake workflow, which calls python scripts that do the pre-processing of each data source, semantic representation, and ultimitely generation of a new edgelist and node file as MGMLink.

## Getting Started

These instructions will provide the necessary environments, programs with installation instructions, and input files in order to run the snakefile, which will run this workflow from end to end. 

### Dependencies
The following dependencies are listed in the environment.yml file, and installed in the installation step. This software has only been tested on Unix based OS systems, not Windows.

```
  - python>=3.8.*
  - tqdm>=4.64.0
  - gensim>=4.2.0
  - numpy>=1.22.4
  - csrgraph>=0.1.28
  - nodevectors>=0.1.23
  - rdflib>=6.2.0
```

## Installation

Clone this repository and move into the main directory.

```
git clone https://github.com/bsantan/MGMLink
cd MGMLink
```

First, snakemake must be installed in a separate environment. For more details, visit https://snakemake.readthedocs.io/en/stable/getting_started/installation.html. Install mamba, which will be used to create the environment, using the following commands:

```
conda install mamba
mamba create -c conda-forge -c bioconda -n snakemake snakemake
conda activate snakemake
```

Next, the activated snakemake environment will be updated with all dependencies with the following command:

```
conda env update --file environment.yml --prune
```

## Running the Script

### Input Directory 
The resources integrated into MGMLink are list below.

#### Files already included in /KG_Resources folder:
- GutMGene: see http://bio-annotation.cn/gutmgene/ for the database and the publication by Cheng et al. for more information, https://doi.org/10.1093/nar/gkab786. The files listed below are located in the /KG_Resources folder of the repo, and will be used in the early stages of the workflow.
```
1. Gut_Microbe_and_Gene-human.txt
2. Gut_Microbe_and_Gene-mouse.txt
3. Gut_Microbe_and_Metabolite-human
4. Gut_Microbe_and_Metabolite-mouse.txt
```
- Microbe Relationships: Another file input in the /KG_Resources folder is a manually curated file of taxonomic relationships among the microbes included in gutMGene as defined by rdf:subClassOf.
```
microbes_taxonomic_relationships.csv
```

#### Files that must be downloaded to include in /KG_Resources folder:
- PheKnowLator: see the GCS bucket https://console.cloud.google.com/storage/browser/pheknowlator/current_build/knowledge_graphs/instance_builds/relations_only/owlnets?pageState=(%22StorageObjectListTable%22:(%22f%22:%22%255B%255D%22))&project=pheknowlator&prefix=&forceOnObjectsSortingFiltering=false, and the publication by Callahan et al. for more information, https://doi.org/10.1101/2020.04.30.071407. The files below must be downloaded from the GCS bucket into the /KG_Resources folder of the repo, and will be used in the early stages of the workflow.
```
1. PheKnowLator_v3.0.2_full_instance_relationsOnly_OWLNETS_NodeLabels.txt
2. PheKnowLator_v3.0.2_full_instance_relationsOnly_OWLNETS_Triples_Identifiers.txt
```


### Command Line Argument 
  
To run the snakemake workflow, execute the following command once the input directory is prepared. This will take ~10 minutes to run:
  
```
snakemake --cores 1 -s Snakefile.yaml --verbose
```

## Expected Outputs

All files will be output to the /Output folder within the repo.
  
### Intermediate Files

```
1. LabelTypes_gutMGene_URI_LABEL_MAP.csv
```
Label type (microbe or other), uri identifier, curie, and name for all new nodes added from gutMGene
```
2. gutMGene_URI_LABEL_MAP.csv
```
Uri identifier, curie, and name fore all new nodes added from gutMGene

```
3. gutMGene_OTU_Pattern_Modifications.csv
```
OWL representation patterns for each assertion type from gutMGene

```
4. gutMGene_new_Properties.csv
```
New relations added not previously part of PheKnowLator KG

```
5. gutMGene_OWLNETS_Triples.csv
```
OWLNETS transformation into triples of OWL assertions from "gutMGene_OTU_Pattern_Modifications.csv" above (transformed into "gutMGene_OWLNETS_Triples_Brackets.txt" to align with PKL standards)

```
6. microbes_Triples.csv
```
Taxonomic relationships represented as triples for all microbes from gutMGene (transformed into "microbes_Triples_Brackets.txt" to align with PKL standards)

```
7. gutMGene_microbes_contextual_labels.csv
```
Node labels for all microbes in MGMLink


```
8. LabelTypes_gutMGene_URI_LABEL_MAP_contextual.csv
```
Node labels for all nodes from gutMGene in MGMLink

```
9. PheKnowLator_v3.0.2_full_instance_relationsOnly_OWLNETS_Triples_Integers_node2vecInput_withGutMGene_withMicrobes.txt
10. PheKnowLator_v3.0.2_full_instance_relationsOnly_OWLNETS_Triples_Integer_Identifier_Map_withGutMGene_withMicrobes.json,
11. PheKnowLator_v3.0.2_full_instance_relationsOnly_OWLNETS_Triples_node2vecInput_cleaned_withGutMGene_withMicrobes.txt
```
Intermediate files necessary for Node2Vec embeddings generation


### KG Files

``` 
1. PheKnowLator_v3.0.2_full_instance_relationsOnly_OWLNETS_NodeLabels_NewEntities.txt
``` 
Node labels for all nodes in MGMLink 

``` 
2. PheKnowLator_v3.0.2_full_instance_relationsOnly_OWLNETS_Triples_Identifiers_withGutMGene_withMicrobes.txt
``` 
Edgelist for MGMLink

``` 
3. PheKnowLator_v3_node2vec_Embeddings.emb
``` 
Node2Vec vector embeddings for MGMLink (128 dimensions)

``` 
4. transe_embedding_mgmlink_embedding_.pkl
``` 
TransE vector embeddings for MGMLink (128 dimensions)
