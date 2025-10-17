from  dgraph_flex import DgraphFlex

obj = DgraphFlex()


# add edges to graph object
obj.add_edge('A', '-->', 'B', color='green', strength=-0.5, pvalue=0.01)
obj.add_edge('B', '-->', 'C', color='red', strength=-.5, pvalue=0.001)
obj.add_edge('C', 'o->', 'E', color='green', strength=0.5, pvalue=0.005)
obj.add_edge('D', 'o-o', 'B')
obj.add_edge('F', '<->', 'B')

# add edges using a list of strings
edges = ['F --> G', 'F o-> H']
obj.add_edges(edges)

# to modify an existing edge
obj.modify_existing_edge('A', 'B', color='green', strength=0.2, pvalue=0.0001)
obj.modify_existing_edge('F', 'G', color='blue', strength=-0.3, pvalue=0.05)
obj.modify_existing_edge('F', 'I', color='blue', strength=-0.3, pvalue=0.05)
obj.save_graph('dgraph_flex/dgflex2')
#obj.save_graph(plot_format='png', plot_name='dgraph_flex/dgflex2')

# modify an existing edge
obj.modify_existing_edge('A', 'B', color='red', strength="-.234", pvalue=0.0001)
obj.save_graph('dgflex_add2')