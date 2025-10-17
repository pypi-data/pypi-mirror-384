#! /usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import os
import glob
import sys
import json
from pathlib import Path
import textwrap
from glob import glob
import yaml

from graphviz import Digraph
import matplotlib.pyplot as plt
# import networkx as nx
# import pandas as pd
# import numpy
# import seaborn as sns


# from dotenv import dotenv_values  # pip install python-dotenv
# import yaml # pip install pyyaml

"""



"""

__version_info__ = ('0', '1', '11')
__version__ = '.'.join(__version_info__)

version_history = \
"""
0.1.11 - in modify_existing_edge, if edge doesn't exist skip instead of raising an error.
        This is to support using a subset of edges in graph (e.g. ancestors) but
        still use the full graph SEM results to modify the edges.
0.1.10 - add directed_only boolean to load_image, save_image, show_image to only load directed edges
0.1.9 - change the handling of arguments for save_graph
0.1.8 - add exclude option to add_edges method to exclude certain edge types
        add support for --- edge in load_graph method
0.1.7 - add add_edges method to add multiple edges at once
0.1.6 - fixed bug with adding the <-> edge type
0.1.5 - change modify_existing_edge to use self.dot object 
0.1.4 - add show_graph method to display graph in jupyter notebook

from dgraph_flex import DgraphFlex

obj = DgraphFlex()
# add edges to graph object
obj.add_edge('A', '-->', 'B', color='green', strength=-0.5, pvalue=0.01)
obj.add_edge('B', '-->', 'C', color='red', strength=-.5, pvalue=0.001)
obj.add_edge('C', 'o->', 'E', color='green', strength=0.5, pvalue=0.005)
obj.add_edge('D', 'o->', 'B', color='purple')
# load into graphviz object and render to window
obj.show_graph()

0.1.3 - have __init__ create the graph dict, new format for graph structure

Example of the new format:
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

Example of how to use the object:

from dgraph_flex import DgraphFlex

# create the graph object
obj = DgraphFlex(verbose=args.verbose)
# add edges to graph object
obj.add_edge('A', '-->', 'B', color='green', strength=-0.5, pvalue=0.01)
obj.add_edge('B', '-->', 'C', color='red', strength=-.5, pvalue=0.001)
obj.add_edge('C', 'o->', 'E', color='green', strength=0.5, pvalue=0.005)
obj.add_edge('B', 'o-o', 'D')
# load into graphviz object
obj.load_graph()
# save the graph to a file
obj.save_graph(plot_format='png', plot_name='dgflex2')


0.1.2 - default resolution of 300
0.1.1 - added GENERAL|gvinit to set graph attributes
0.1.0 - initial version  
"""
    


class DgraphFlex:
    
    def __init__(self, **kwargs):
        
        # initialize the graph
        self.graph = {
            "GENERAL": {
                "version": 2.0,
                "framework": "dgraph_flex",
                "gvinit": {
                    "nodes": {
                        "shape": "oval",
                        "color": "black",
                    },
                    # "edges": {
                    #     "color": "black",
                    #     "style": "solid",
                    # }
                }
            },
            "GRAPH": {
                "edges": {
                }
            }   
        }
        

        # load self.config
        self.config = {}
        for key, value in kwargs.items():
            self.config[key] = value

        # load the graph description from the yaml file
        # self.load_graph()
        
        # expose the edges 
        self.edges = self.graph['GRAPH']['edges']

        pass


    def read_yaml(self, yamlpath, version=2.0):
        "read in the yaml config file"
        with open(yamlpath, 'r') as file:
            self.graph = yaml.safe_load(file)

        if self.graph['GENERAL']['version'] > version:
            print(f"Error: Supports up to {version}, this is version {self.graph['GENERAL']['version']}")
            sys.exit(1)

        return self.graph
            
    def cmd(self, cmd):
        if cmd == 'plot':
            self.read_yaml(self.config['yamlpath'])
            self.load_graph(res=100)
            self.save_graph(plot_format='png', plot_name='dgflex')
            
    def load_graph(self, graph=None, plot_format='png',res=300, directed_only=False):
        """
        Load a graph definition from a yaml file into a graphviz object
        
        
        set the edge attributes starting from the first character to the third character
        
        --> == These indicate a direct causal influence. For example, A --> B means that variable A directly causes variable B
        o-> == Indicates that either A causes B, or there's an unobserved confounder affecting both A and B, or both.
        <-> == Indicates the presence of an unobserved confounder affecting both variables.
        --- == These represent a relationship between variables, but the direction of causality is uncertain.
        o-o == Indicates that either A causes B, B causes A, or there's an unobserved confounder, or any combination of these.
        
        args:
            graph: The graph object to load. If None, uses the graph from the object.
            plot_format: The format to save the graph in (e.g., 'png', 'pdf').
            res: The resolution of the plot.
            directed_only: if True only load directed_edges e.g. -->, o->
        """    
        
        
        # create the graph object
        self.dot = Digraph( format=plot_format)
        
        # set default resolution of 600 
        self.dot.format = plot_format   
        self.dot.attr(dpi=str(res)) 
        
        # if GENERAL|gvinit is present, set the graph attributes
        if self.graph.get('GENERAL', False):
            if self.graph['GENERAL'].get('gvinit', False):
                # check for nodes
                if 'nodes' in self.graph['GENERAL']['gvinit']:
                    self.dot.node_attr.update(self.graph['GENERAL']['gvinit']['nodes'])
                pass
                # for key, value in self.graph['GENERAL']['gvinit'].items():
                #     self.dot.attr(key, value)
                
                    
        # set the node attributes
        #self.dot.attr('node', shape='oval')
        
        if graph is None:
            # use the graph from the object
            graph = self.graph
            
        edges = graph['GRAPH']['edges']
        # start with the edges in self.graph
        for name, edge in edges.items():
            
            # extract the source, edge_type and target from the key
            source, edge_type, target = name.split(' ')
            
            # check if directed_only
            if directed_only and edge_type not in ['-->', 'o->']:
                continue
            
            # edge is a tuple of (key, value)
            edge_attr = {
                "dir": "both",
                "label": "",
            }
            
            # set default values for arrowhead and arrowtail
            arrowhead = 'normal'
            arrowtail = 'none'
            

            # set the arrowhead and arrowtail based on the edge type
            if edge_type == 'o->':
                arrowtail='odot'
            elif edge_type == 'o-o':
                arrowtail='odot'
                arrowhead='odot'
            elif edge_type == '<->':
                arrowtail='normal'
            elif edge_type == '---':
                arrowhead='none'
                arrowtail='none'

                
            # create info structure to ease access to edge information
            label = ''
            color = 'black'
            
            if edge.get('properties',False):
                if edge['properties'].get('strength', None) is not None:
                    label = f"{edge['properties']['strength']}"
                # check for pvalue
                if edge['properties'].get('pvalue', None) is not None:
                    label += f"\n{edge['properties']['pvalue']}"
                
            if edge.get('gvprops', False):
                # set color    
                if edge['gvprops'].get('color', None) is not None:
                    color = edge['gvprops']['color']
                    
            # create the edge object
            self.dot.edge(  source, target,
                            arrowtail=arrowtail,
                            arrowhead=arrowhead,
                            dir='both',
                            label=label,
                            color=color,)
                            #**edge_attr)
                                    

            pass
            
        # render
        
        # print(self.dot.source)
    
    def show_graph(self,format='png',res=72, directed_only=False):
        """
        Display the graph in a Jupyter notebook.
        """
        # Set the desired output format for Jupyter to PNG
        import graphviz
        # Set the format to PNG for Jupyter
        graphviz.set_jupyter_format(format)
        # load the graph into the graphviz object
        self.load_graph(res=res,directed_only=directed_only)
        return self.dot
        

    def save_graph(self, 
                   plot_pathname: str,
                   plot_format: str ='png',
                   res: int =300, 
                   cleanup:bool =True,
                   directed_only = False):
        """
        Save the graph to a specified file in the specified format.
        
        This method renders the graph to a file with the specified pathname and format.
        Both a graphics file ('png') and a Graphviz source file ('dot') are saved. The 
        graphviz source file can be useful for further editing or inspection of the graph structure.
        
        Args:
            plot_pathname: The pathname of the output file (without extension).
            plot_format: The format to save the graph in (e.g., 'png', 'pdf'). Defaults to 'png'.
            res: The resolution of the plot. Defaults to 300.
            cleanup: Whether to clean up the intermediate files after rendering. Defaults to True.

        """
        
        self.load_graph(res=res, directed_only=directed_only)
        # save gv source
        self.gv_source = self.dot.source
        # save to a file with a .dot extension
        with open(f"{plot_pathname}.dot", 'w') as f:
            f.write(self.gv_source)



        self.dot.format = plot_format
        self.dot.render(filename = plot_pathname,
                        format=plot_format,
                        cleanup=cleanup,
                        
                        )
        pass
    
    def add_edge_lowlevel(self, src, edge_type, tar, **kwargs):
        """Adds an edge to dgraph object.

        Args:
            src: The source node name.
            edge_type: The type of edge (e.g., '-->', 'o->', 'o-o', '<->','---').
            tar: The target node name.
            **kwargs: Additional attributes for the edge (e.g., color='blue', style='dotted').
        """
        # Check if the edge already exists
        if f"{src} {edge_type} {tar}" in self.edges:
            print(f"Edge '{src} {edge_type} {tar}' already exists.")
            raise ValueError(f"Edge '{src} {edge_type} {tar}' already exists.")
            return
        
        # add the edge to the graph dictionary
        # Check if the edge type is valid
        if edge_type not in ['o->', 'o-o', '<->', '---','-->']:
            print(f"Invalid edge type '{edge_type}'.")
            raise ValueError(f"Invalid edge type '{edge_type}'.")
            return
        # Add the edge to the graph dictionary
        if 'properties' not in kwargs:
            kwargs['properties'] = {}
        if 'gvprops' not in kwargs:
            kwargs['gvprops'] = {}
  

        # Create the edge
        self.edges[f"{src} {edge_type} {tar}"] = kwargs

        pass

    def add_edge(self, src, edge_type, tar,  **kwargs):
        """Adds an edge to the graph with the specified attributes.

        Args:
            src: The source node name.
            edge_type: The type of edge (e.g., 'o->', 'o-o', '<->').
            tar: The target node name.
            **kwargs: Additional attributes for the edge (e.g., color='blue', style='dotted').
        """
        newargs = {
            "gvprops": {
                "color": "black",
            },
            "properties": {
                "strength": None,
                "pvalue": None,
            }
        }

        # check if color is in kwargs
        if 'color' in kwargs:
            # set the color
            newargs['gvprops']['color'] = kwargs['color']
        # check if strength is in kwargs
        if 'strength' in kwargs:
            # set the strength
            newargs['properties']['strength'] = kwargs['strength']
        # check if pvalue is in kwargs
        if 'pvalue' in kwargs:
            # set the pvalue
            newargs['properties']['pvalue'] = kwargs['pvalue']
        self.add_edge_lowlevel(src, edge_type, tar, **newargs)
        

        
        pass

    def add_edges(self, edges, exclude=[]):
        """
        Adds multiple edges to the graph.

        Args:
            edges: A list of strings, where each string contains 
                the src edge and tar.  For example: ['A --> B', 'B o-> C', 'C o-o D']
            exclude: A list of edge types to exclude (e.g., ['<->', '---']).
        """
        for edge in edges:
            src, edge_type, tar = edge.split()
            if edge_type not in exclude:
                kwargs = {}
                self.add_edge(src, edge_type, tar, **kwargs)
            
        pass
    def modify_existing_edge(self, from_node, to_node,
                             format: str="0.3f",**kwargs):
        """Modifies the attributes of an existing edge in a Graphviz graph.

        Args:
            from_node: The name of the starting node of the edge.
            to_node: The name of the ending node of the edge.
            format: The format for the strength and  pvalue (default is "0.3f").
            **kwargs: The attributes to modify (e.g., color='blue', style='dotted').
        """

        for edge in self.graph['GRAPH']['edges'].keys():
            # split the edge into its components
            source, type, target = edge.split()

            # check if the edge matches the from_node and to_node
            if source == from_node and target == to_node:
                # modify the edge attributes in kwargs
                for key, value in kwargs.items():
                    if key == 'color':
                        self.graph['GRAPH']['edges'][edge]['gvprops']['color'] = value
                    elif key == 'strength':
                        strength = value
                        if isinstance(strength,float) and format:
                           # convert to string with 3 decimal places
                            strength = f"{strength:.3f}"
                        self.graph['GRAPH']['edges'][edge]['properties']['strength'] = strength
                    elif key == 'pvalue':
                        pvalue = value
                        if isinstance(pvalue,float) and format:
                            # convert to string with 3 decimal places
                            pvalue = f"{pvalue:.3f}"
                        self.graph['GRAPH']['edges'][edge]['properties']['pvalue'] = pvalue

                return
        
        # instead of raising an error, just skip if edge not found and give a warning
        print(f"Warning: Edge '{from_node} {type} {to_node}' not found. Skipping modification.")
        
        #raise ValueError(f"Edge '{from_node} {type} {to_node}' not found.")

        pass
            
if __name__ == "__main__":
    
    # provide a description of the program with format control
    description = textwrap.dedent('''\
    
    Class to support directed graph display in support of causal structure analysis.
    
 
    ''')
    
    parser = argparse.ArgumentParser(
        description=description, formatter_class=argparse.RawTextHelpFormatter)

    # handle a single file on command line argument
    parser.add_argument('--file',  type=str,  help='input file')
    

        
    parser.add_argument("--cmd", type = str,
                    help="cmd - [plot], default plot",
                    default = 'plot')
    
    parser.add_argument("-H", "--history", action="store_true", help="Show program history")
     
    # parser.add_argument("--quiet", help="Don't output results to console, default false",
    #                     default=False, action = "store_true")  
    
    parser.add_argument("--verbose", type=int, help="verbose level default 2",
                         default=2) 
        
    parser.add_argument('-V', '--version', action='version', version=f'%(prog)s {__version__}')

    args = parser.parse_args()
            
    if args.history:
        print(f"{os.path.basename(__file__) } Version: {__version__}")
        print(version_history)
        exit(0)

    obj = DgraphFlex(  yamlpath = args.file, verbose = args.verbose)

    obj.cmd('plot')

    # create the graph object
    obj = DgraphFlex()
    # add edges to graph object
    obj.add_edge('A', '-->', 'B', color='green', strength=-0.5, pvalue=0.01)
    obj.add_edge('B', '-->', 'C', color='red', strength=-.5, pvalue=0.001)
    obj.add_edge('C', 'o->', 'E', color='green', strength=0.5, pvalue=0.005)
    obj.add_edge('B', 'o-o', 'D')
    # save the graph to a file
    obj.save_graph(plot_format='png', plot_name='dgflex2',res=300)
    pass

