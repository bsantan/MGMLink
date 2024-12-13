# Path Search

This repository enables the search for a path between a source and target node, using the MGMLink knowledge graph.

## Getting Started 

These instructions will provide the necessary environments to execute the creating_subgraph_from_KG.py script. 

### Dependencies
The following dependencies are listed in the environment.yml file, and installed in the installation step. This software has only been tested on Unix based OS systems, not Windows.
```
Python>=3.8.3
tqdm>=4.64.0
gensim>=4.2.0
numpy>=1.22.4
scipy>=1.8.1
py4cytoscape>=1.3.0
csrgraph>=0.1.28
nodevectors>=0.1.23
igraph>=0.9.10
```
## Installation

```
git clone https://github.com/MGMLink
```

First install mamba, which will be used to create the environment. To create an environment with all dependencies and activate the environment, run the following commands:

```
conda install mamba

mamba env create -f environment.yml
conda activate MGMLink_PathSearch
```

Run the MGMLink Snakefile to first generate the knowledge graph.

Ensure that Cytoscape (any version later than 3.8.0) is up and running before continuing.

### Defaults
  
The following values will be used if not otherwise specified:
- embedding dimensions: the dimension of embeddings of the knowledge graph that will be generated
 --embedding-dimensions <int> (Default 128)
- embedding method: the method from which to create the embeddings (transe and node2vec supported), when "both" is specified both  methods will be run
 --embedding-method transe (Default node2vec)
- weights: edges will not be weighted unless otherwise specified. When set to True, edges defined in an interactive search will be excluded from the path search. 
  --weights True (Default False)
- search type: the shortest path algorithm used (contained within the python-igraph package), when both is spefied that both "all" and "out" will be used
 --search-type out (Default "all")
- first order nodes: the source node of the shortest path search will include all microbial first order neighbors of the given taxa
 --first-order-nodes True (Default "False")
- num paths output: number of path found by a given search methodology to be output as a subgraph_#.csv file
 --num-paths-output <int> (Default 20)

### Command Line Argument: subgraph generation 
  
The following files and directories must exist to execute this command. 

1. The MGMLink knowledge graph.

2. The desired source and target concepts must exist in the input directory as the "_example_input.csv" in the format:

```
source|target
faecalibacterium_prausnitzii|parkinson disease
```  
 
3. The metapaths directory must exist with the expected metapaths. We have committed source controlled versions and hardcoded the following selection:

- faecalibacterium_prausnitzii : Input_Metapaths.csv
- others: Input_Metapaths_Long.csv

This is an example minimal input and output directory (serves as both), assuming that embeddings have already been generated which is expected by the Snakemake workflow:

```
├── Output
│   ├── PheKnowLator_v3.0.2_full_instance_relationsOnly_OWLNETS_NodeLabels_NewEntities.txt
│   ├── PheKnowLator_v3.0.2_full_instance_relationsOnly_OWLNETS_Triples_Identifiers_withGutMGene_withMicrobes.txt
│   ├── PheKnowLator_v3.0.2_full_instance_relationsOnly_OWLNETS_Triples_Identifiers_withGutMGene_withMicrobes.txt
│   ├── PheKnowLator_v3.0.2_full_instance_relationsOnly_OWLNETS_Triples_Integer_Identifier_Map_withGutMGene_withMicrobes.json
│   ├── PheKnowLator_v3.0.2_full_instance_relationsOnly_OWLNETS_Triples_Integer_Identifier_Map_withGutMGene_withMicrobes.txt
│   ├── PheKnowLator_v3.0.2_full_instance_relationsOnly_OWLNETS_Triples_Integers_node2vecInput_withGutMGene_withMicrobes.txt
│   ├── PheKnowLator_v3.0.2_full_instance_relationsOnly_OWLNETS_Triples_node2vecInput_cleaned_withGutMGene_withMicrobes.txt
│   ├── PheKnowLator_v3_node2vec_Embeddings.emb
│   ├── transe_embedding_mgmlink_embedding_.pkl
│   └── manuscript_example_input.csv
└──  manuscript_example_input.csv
├── metapaths
│   ├── Input_Metapaths.csv
│   └── Input_Metapaths_Long.csv
```

To run the script, execute the following command once the input directory is prepared:
  
```
python creating_subgraph_from_KG.py --input-dir INPUTDIR --output-dir OUTPUTDIR --knowledge-graph mgmlink --first-order-nodes True --search-type both --embedding-method both
```

Enabling the first-order-nodes option will ensure that the microbial first order neighbors are found as the source node. Providing "both" for the search type will produce paths from an undirected shortest path search (all) and a directed shortest path search (out). Providing "both" for the embedding method will prioritize paths using embeddings build from both Node2Vec and TransE. 

## Expected Outputs

The algorithm will first assign the given concepts to nodes in the graph and output the following input nodes files:

- _experimental_data_Input_Nodes_.csv
- _experimental_data_contextual_Input_Nodes_.csv

where the contextual_Input_Nodes file will have the microbes mapped to their microbial first order nodes if first-order-nodes is enabled.

Below is an example for one given source, target pair. The set of folders with the "CosineSimilarity_" substring are the top prioritized paths, where a blank file will be output if no paths exist, for:
- each method (Shortest_Path or Metapath)
- each search-type (all or out) or each metapath (represented as an integer defined in the Evaluation_Files/Metapath_Key.csv, or metapath_num)
- each unique pair found from the microbial first order neighbor search (unique_id_pair_num)

By default, 20 paths will be output for each combination above distinguished with an integer (unique_subgraph_num). To change this, provide the desired number using the --num-paths-output <int> option. 

```
├── node2vec OR transe
│   ├── CosineSimilarity_Metapath_Path<metapath_num>_<unique_id_pair_num>
│   │   ├── Subgraph.csv
│   │   ├── Subgraph_Visualization.png
│   │   └── Subgraph_attributes.noa
│   ├── CosineSimilarity_Shortest_Path_all_<unique_id_pair_num>
│   │   ├── Subgraph.csv
│   │   ├── Subgraph_Visualization.png
│   │   └── Subgraph_attributes.noa
│   ├── CosineSimilarity_Shortest_Path_out_<unique_id_pair_num>
│   │   ├── Subgraph.csv
│   │   ├── Subgraph_Visualization.png
│   │   └── Subgraph_attributes.noa
│   ├── Metapath_Path<metapath_num>
│   │   └── All_Paths_<unique_id_pair_num>
│   │       ├── Subgraph_<unique_subgraph_num>.csv
│   │       ├── Subgraph_<unique_subgraph_num>_attributes.csv
│   ├── Shortest_Path_all
│   │   └── All_Paths_<unique_id_pair_num>
│   │       ├── Subgraph_<unique_subgraph_num>.csv
│   │       ├── Subgraph_<unique_subgraph_num>_attributes.csv
│   └── Shortest_Path_out
│   │   └── All_Paths_<unique_id_pair_num>
│   │       ├── Subgraph_<unique_subgraph_num>.csv
│   │       ├── Subgraph_<unique_subgraph_num>_attributes.csv
```

### Subgraph Files
  
The creating_subgraph_from_KG.py script will always generate the following files:
  
### Subgraph

A .csv file which shows all source and target nodes found in the path search that include the source and target nodes.

```
S|P|O|S_ID|P_ID|O_ID
CONTEXTUAL faecalibacterium prausnitzii: lower digestive tract Homo sapiens|PROPERTY metabolizes|cholesterol|http://github.com/callahantiff/PheKnowLator/pkt/12cc7f6b2f2087391daca2371864d803|http://github.com/callahantiff/PheKnowLator/pkt/9632542199d7d436bdb9e43a46b05929|http://purl.obolibrary.org/obo/CHEBI_16113
cholesterol|is substance that treats|Dementia|http://purl.obolibrary.org/obo/CHEBI_16113|http://purl.obolibrary.org/obo/RO_0002606|http://purl.obolibrary.org/obo/HP_0000726
Parkinson disease|has phenotype|Dementia|http://purl.obolibrary.org/obo/MONDO_0005180|http://purl.obolibrary.org/obo/RO_0002200|http://purl.obolibrary.org/obo/HP_0000726
```
  
### Evaluation Files

Below is an example of the evaluation files output for the above example. 

```
├── node2vec OR transe
│   ├── Evaluation_Files
│   │   ├── Metapaths_Key.csv
│   │   ├── num_paths_Metapath.csv
│   │   ├── num_paths_Shortest_Path.csv
│   │   ├── path_list_comparison_distribution.png
│   │   ├── path_list_comparison_distribution_statistics.txt
│   │   ├── paths_list_CosineSimilarity_Metapath_Path<metapath_num>_<unique_id_pair_num>.csv
│   │   ├── paths_list_CosineSimilarity_Shortest_Path_all__<unique_id_pair_num>.csv
│   │   ├── paths_list_CosineSimilarity_Shortest_Path_out__<unique_id_pair_num>.csv
```

### Command Line Argument: embeddings comparison

To determine the statistical difference between the two embeddings methods (transe and node2vec), the sugraph generation command must have been run for both embeddings methods for at least one pair and the above Evaluation_Files directory must exist under each embedding method subfolder. The script also assumes that both path search methodologies have been run, Shortest_Path and Metapath. 

To run the script, execute the following command once the input directory is prepared:
  
```
python embeddings_comparison.py --output-dir OUTPUTDIR --input-dir INPUTDIR
```

The OUTPUTDIR will be the directory for the desired pair, and the INPUTDIR will be the directory where the directory that containes the input nodes file, for example:

```
python embeddings_comparison.py --output-dir "../Output/faecalibacterium_prausnitzii__Parkinson_disease" --input-dir "../Output"
```

## Expected Outputs

Below is the expected for the given example:

├── faecalibacterium_prausnitzii__Parkinson_disease
│   ├── Metapath_rank_correlation_embeddings.csv
│   ├── Metapath_rank_correlation_embeddings_statistics.txt
│   ├── Shorest_Path_rank_correlation_embeddings_statistics.txt
│   ├── Shortest_Path_rank_correlation_embeddings.csv

### Command Line Argument: All paths comparison

To output the metadata for all paths found from a given example_input file, the sugraph generation command must have been run. The algorithm does not assume that both embeddings methods have been run or that both path search methods/search types have been run. 

To run the script, execute the following command once the input directory is prepared:
  
```
python all_paths_output_evaluation.py --output-dir --output-dir OUTPUTDIR --input-nodes-file INPUTNODESFILE
```

The OUTPUTDIR will be the directory with all pair outputs, and the INPUTNODESFILE will be the previously transformed nodes file by the subgraph generation command, for example:

```
python all_paths_output_evaluation.py --output-dir "../Output" --input-nodes-file "../Output/_experimental_data_contextual_Input_Nodes_.csv"
```

## Expected Outputs

Below is the expected for the given example:

├── faecalibacterium_prausnitzii__Parkinson_disease
│   ├── All_Paths_Results.csv

### Command Line Argument: subgraph visualization

To create a cytoscape image for a given subgraph, only the subgraph file path and the input nodes file need to be provided. Cytoscape must be running for this command.


To run the script, execute the following command once the input directory is prepared:
  
```
python visualize_in_cytoscape.py --input-nodes-file INPUTNODESFILE --input-subgraph-file INPUTSUBGRAPHFILE
```

Where the input subgraph file points to a specific subgraph to be visualized, and the input nodes file is used to color the nodes based on them being input or intermediate nodes. For example:

```
python visualize_in_cytoscape.py --input-nodes-file  "Output/_experimental_data_contextual_Input_Nodes_.csv" --input-subgraph-file "Output/streptococcus__inflammatory_bowel_disease/Shortest_Path_out/All_Paths_0/Subgraph_14.csv"
```

## Expected Outputs

The command will output a Subgraph_<unique_subgraph_num>.png where the unique subgraph num matches the input subgraph file based on the created graph in Cytoscape.s


