# dgraph_flex

Package to support flexible storage of directed graphs, specifically for the support of
directed graphs and causal structure analysis.

Changed edges from a list to a dict using the edge name src --> tar
to make it easier to address, query and set

## sample usage

```
from dgraph_flex import DgraphFlex

# create the graph object
obj = DgraphFlex()
# add edges to graph object
obj.add_edge('A', '-->', 'B', color='green', strength=-0.5, pvalue=0.01)
obj.add_edge('B', '-->', 'C', color='red', strength=-.5, pvalue=0.001)
obj.add_edge('C', 'o->', 'E', color='green', strength=0.5, pvalue=0.005)
obj.add_edge('B', 'o-o', 'D')
obj.add_edge('F', '<->', 'B')

# to modify an existing edge
obj.modify_existing_edge('A', 'B', color='green', strength=0.2, pvalue=0.0001)

# Save the graph to a file 'sample_graph' with a default format of png and  resolution of 300
# The format suffix is automatically added to the provided filename.  A graphviz source 'dot'
# file is also generated. This can be edited and rerendered with the 'dot' command.

obj.save_graph('sample_graph')
```

Here is the generated graph

![Example Graph](https://github.com/kelvinlim/dgraph_flex/blob/main/dgraph_flex/dgflex2.png)

## for use in jupyter notebook

```
from dgraph_flex import DgraphFlex

obj = DgraphFlex()
# add edges to graph object
obj.add_edge('A', '-->', 'B', color='green', strength=-0.5, pvalue=0.01)
obj.add_edge('B', '-->', 'C', color='red', strength=-.5, pvalue=0.001)
obj.add_edge('C', 'o->', 'E', color='green', strength=0.5, pvalue=0.005)
obj.add_edge('D', 'o-o', 'B')
obj.add_edge('F', '<->', 'B')

# render to window
obj.show_graph()

```

## sample yaml file

Here is a sample yaml file describing a graph

```yaml

GENERAL:
  version: 2.0
  framework: dgraph_flex
  gvinit:  # global graphviz initialization
    nodes:
      shape: oval
      color: black

GRAPH:
  edges: # Use indentation for the dictionary under 'edges'
    "A --> B": # Key for the first edge
      properties: # Indent for the 'properties' dictionary
        strength: 0.5
        pvalue: 0.01
      gvprops: # Indent for the 'gvprops' dictionary
        color: green
    "B --> C": # Key for the second edge
      properties: # Indent for 'properties'
        strength: -0.5
        pvalue: 0.001
      gvprops: # Indent for 'gvprops'
        color: red
    "C o-> E": # Key for the third edge
      properties: # Indent for 'properties'
        strength: 0.5
        pvalue: 0.0005
      gvprops: # Indent for 'gvprops'
        color: green
    "B o-o D": # Key for the fourth edge
      properties: # Indent for 'properties'
        strength: 0.5
        pvalue: 0.0005
      gvprops: # Indent for 'gvprops'
        color: black

```

Here is python code that reads in the graph and outputs a png

```python

from dgraph_flex import DgraphFlex

obj = DgraphFlex(yamlpath='graph_sample.yaml')
obj.read_yaml(self.config['yamlpath'])
obj.load_graph()



```

## unit tests

```
python -m unittest tests/*.py
```

## build

```
python -m build

# upload
twine upload dist/*

```
