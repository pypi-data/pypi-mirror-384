# Created on 26/07/2025
# Author: Frank Vega

import itertools

import networkx as nx
import furones.algorithm as algo

def graph_coloring(graph):
    """
    Find the minimum chromatic number coloring using heuristic approach.
    
    This function implements a heuristic algorithm for graph coloring that
    iteratively finds independent sets and assigns colors to them.
    
    Args:
        graph: NetworkX undirected graph
    
    Returns:
        Dictionary with nodes as keys and colors (0, 1, 2, ...) as values
    """
    
    def _is_complete_graph(G):
        """Returns True if G is a complete graph.
        
        A complete graph is one where every pair of distinct nodes is connected
        by a unique edge.
        
        Args:
            G (nx.Graph): A NetworkX Graph object to check.
        
        Returns:
            bool: True if G is a complete graph, False otherwise.
        """
        n = G.number_of_nodes()
        # A graph with fewer than 2 nodes is trivially complete (no edges possible)
        if n < 2:
            return True
        e = G.number_of_edges()
        # A complete graph with n nodes has exactly n*(n-1)/2 edges
        max_edges = (n * (n - 1)) / 2
        return e == max_edges
    
    # Validate input type - must be a NetworkX Graph
    if not isinstance(graph, nx.Graph):
        raise ValueError("Input must be an undirected NetworkX Graph.")
   
    # Handle trivial cases where no chromatic number is needed
    # Empty graph or graph with no edges requires no coloring
    if graph.number_of_nodes() == 0 or graph.number_of_edges() == 0:
        return {} 
   
    # Create a working copy to avoid modifying the input graph
    # This allows us to safely remove nodes/edges during processing
    working_graph = graph.copy()
   
    # Preprocessing: Clean the graph by removing self-loops
    # Self-loops don't affect coloring but can interfere with algorithms
    working_graph.remove_edges_from(list(nx.selfloop_edges(working_graph)))
   
    # Check if the current working graph is bipartite (2-colorable)
    # Bipartite graphs can be colored with exactly 2 colors, which is optimal
    if nx.bipartite.is_bipartite(working_graph):
        # Use NetworkX's built-in bipartite coloring algorithm
        # This returns a dictionary with nodes colored as 0 or 1
        return nx.bipartite.color(working_graph)

    # Initialize the coloring dictionary and color counter
    approximate_coloring = {}
    current_color = -1  # Will be incremented to 0 in first iteration
    
    # Main coloring loop: continue until all nodes are colored
    while working_graph:
        current_color += 1  # Move to next color
        
        # Find isolated nodes (degree 0) - these can all share the same color
        independent_set = set(nx.isolates(working_graph))
        # Remove isolated nodes from working graph
        working_graph.remove_nodes_from(independent_set)
        
        # Check if remaining graph is complete (clique)
        if _is_complete_graph(working_graph):
            # Assign current color to all nodes in the independent set
            approximate_coloring.update({u:current_color for u in independent_set})
            # For complete graphs, each node needs a unique color
            # Assign consecutive colors to all remaining nodes
            approximate_coloring.update({u:(k + current_color) for k, u in enumerate(working_graph.nodes())})
            break  # All nodes colored, exit loop
        else:
            # Find an independent set (set of non-adjacent nodes)
            # This set can all be colored with the current color
            independent_set.update(algo.find_independent_set(working_graph))
            
            # Assign current color to all nodes in the independent set
            approximate_coloring.update({u:current_color for u in independent_set})
            
            # Remove colored nodes from working graph for next iteration
            working_graph = working_graph.subgraph(set(working_graph) - independent_set).copy()
    return approximate_coloring
    

def is_valid_coloring(graph, coloring):
    """
    Check if a coloring is valid (no adjacent nodes have the same color).
    
    Args:
        graph: NetworkX undirected graph
        coloring: Dictionary mapping node -> color
    
    Returns:
        True if coloring is valid, False otherwise
    """
    for u, v in graph.edges():
        if coloring[u] == coloring[v]:
            return False
    return True

def brute_force_graph_coloring(graph):
    """
    Find the minimum chromatic number coloring using brute force approach.
   
    Args:
        graph: NetworkX undirected graph
    
    Returns:
        Dictionary with nodes as keys and colors (0, 1, 2, ...) as values
    """
    if len(graph.nodes()) == 0:
        return {}
    
    nodes = list(graph.nodes())
    n = len(nodes)
    
    def backtrack(node_idx, coloring, num_colors):
        if node_idx == n:
            return True
        
        current_node = nodes[node_idx]
        
        for color in range(num_colors):
            # Check if this color conflicts with already colored neighbors
            valid = True
            for neighbor in graph.neighbors(current_node):
                if neighbor in coloring and coloring[neighbor] == color:
                    valid = False
                    break
            
            if valid:
                coloring[current_node] = color
                if backtrack(node_idx + 1, coloring, num_colors):
                    return True
                del coloring[current_node]
        
        return False
    
    # Try increasing number of colors until we find a solution
    for num_colors in range(1, n + 1):
        coloring = {}
        if backtrack(0, coloring, num_colors):
            return coloring
    
    raise RuntimeError("No valid coloring found")

def graph_coloring_approximation(graph):
    """
    Find the minimum chromatic number coloring using greedy approach.
   
    Args:
        graph: NetworkX undirected graph
    
    Returns:
        Dictionary with nodes as keys and colors (0, 1, 2, ...) as values
    """
    
    if graph.number_of_nodes() == 0 or graph.number_of_edges() == 0:
        return {}

    coloring = nx.coloring.greedy_color(graph)
    return coloring