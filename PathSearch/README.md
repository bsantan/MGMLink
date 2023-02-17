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
conda activate Cartoomics
```

Run the MGMLink Snakefile to first generate the knowledge graph.

Ensure that Cytoscape (any version later than 3.8.0) is up and running before continuing.

### Defaults
  
The following values will be used if not otherwise specified:
- embedding dimensions: embeddings of the knowledge graph will be generated using node2vec of dimension 128, unless otherwise specified
  --embedding-dimensions <int> (Default 128)
- weights: edges will not be weighted unless otherwise specified. When set to True, edges defined in an interactive search will be excluded from the path search. 
  --weights True (Default False)
- search type: the shortest path algorithm used (contained within the python-igraph package) will search for paths in all directions, unless otherwise specified
  --search-type one (Default "all")
  --pdp-weight int (Default "0.4")
 - first order nodes: the source node of the shortest path search will include all neighbors of the given microbe, excluding related taxa or anatomical entities
  --first-order-nodes True (Default "False")
  
  ### Command Line Argument: subgraph generation 
  
The MGMLink knowledge graph must be located in the input directory, and the desired source and target concepts must also exist in the input directory as the "_example_input.csv" in the format:

```
source|target
faecalibacterium_prausnitzii|parkinson disease
```  
 
To run the script, execute the following command once the input directory is prepared:
  
```
python creating_subgraph_from_KG.py --input-dir INPUTDIR --output-dir OUTPUTDIR --knowledge-graph mgmlink
```

You will then be asked to interactively match the input source and target concepts to the desired nodes within the knowledge graph.

## Expected Outputs
  
### Subgraph Files
  
The creating_subgraph_from_KG.py script will always generate the following files:
  
### Subgraph
  
A .csv file which shows all source and target nodes found in the path search that include the source and target nodes.

```
S|P|O
CONTEXTUAL faecalibacterium prausnitzii: lower digestive tract Mus musculus|indirectly negatively regulates activity of|hdac3
diazinon|interacts with|hdac3
diazinon|is substance that treats|Parkinson disease
```
  
  
