# These functions provide utilites for working with directed graphs (nx.DiGraph).

import networkx as nx


def remove_self_loops(graph):
    """
    Remove all self looping edges from a graph

    See https://stackoverflow.com/questions/49427638/removing-self-loops-from-undirected-networkx-graph
    """
    new_graph = graph.copy()
    new_graph.remove_edges_from(nx.selfloop_edges(new_graph))
    return new_graph


def split_graph_into_subgraphs(graph):
    """
    Return subgraphs of a graph, i.e. no subgraph shares an edge or node with any other subgraph.
    """
    return [graph.subgraph(c).copy() for c in nx.weakly_connected_components(graph)]


def get_all_successor_nodes(graph, node):
    """
    Get a set of all nodes which succeed the given node, including the given node itself.
    """
    nodes = nx.descendants(graph, source=node)
    nodes.add(node)
    return nodes


def get_successor_graph(graph, node):
    """
    Get a subgraph of the given graph, containing only the given node and its successors.
    """
    nodes = get_all_successor_nodes(graph, node)
    return graph.subgraph(nodes)


def get_all_predecessor_nodes(graph, node):
    """
    Get a set of all nodes which preceed the given node, including the given node itself.
    """
    nodes = nx.ancestors(graph, source=node)
    nodes.add(node)
    return nodes


def get_predecessor_graph(graph, node):
    """
    Get a subgraph of the given graph, containing only the given node and its predecessors.
    """
    nodes = get_all_predecessor_nodes(graph, node)
    return graph.subgraph(nodes)


def get_ordered_objects(graph):
    """
    Get a list of all objects in a given graph, ordered topologically.
    """
    return list(nx.topological_sort(graph))


def filter_graph(graph, nodes, mode):
    """
    Filter a graph to contain only the given nodes and additional nodes, depending on mode.
    mode = 'given_nodes_only', 'include_predecessors', 'include_successors', 'include_both'
    See docstring of called functions for details.
    """
    if mode.lower() == "given_nodes_only":
        return filter_graph_given_only(graph, nodes)
    elif mode.lower() == "include_predecessors":
        return filter_graph_include_predecessors(graph, nodes)
    elif mode.lower() == "include_successors":
        return filter_graph_include_successors(graph, nodes)
    elif mode.lower() == "include_both":
        return filter_graph_include_both(graph, nodes)
    else:
        raise ValueError(
            f"Given mode [ '{mode}' ] not supported. Supported modes are 'given_nodes_only', 'include_predecessors', 'include_successors', 'include_both'."
        )


def filter_graph_given_only(graph, nodes):
    """
    Filter a graph to contain only the given nodes.
    """
    return graph.subgraph(nodes).copy()


def filter_graph_include_predecessors(graph, nodes):
    """
    Filter a graph to contain only the given nodes and any nodes which preceed these nodes.
    """
    predecessor_nodes = set()
    for n in nodes:
        if n not in predecessor_nodes:
            predecessor_nodes.update(get_all_predecessor_nodes(graph, n))
    return graph.subgraph(predecessor_nodes).copy()


def filter_graph_include_successors(graph, nodes):
    """
    Filter a graph to contain only the given nodes and any nodes which succeed these nodes.
    """
    successor_nodes = set()
    for n in nodes:
        if n not in successor_nodes:
            successor_nodes.update(get_all_successor_nodes(graph, n))
    return graph.subgraph(successor_nodes).copy()


def filter_graph_include_both(graph, nodes):
    """
    Filter a graph to contain only the given nodes and any nodes which succeed or preceed these nodes.
    """
    return nx.compose(
        filter_graph_include_predecessors(graph, nodes),
        filter_graph_include_successors(graph, nodes),
    )
