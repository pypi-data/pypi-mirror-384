import logging
from typing import List

import matplotlib
import networkx as nx
from acedeploy.services.dependency_parser import DependencyParser
from aceutils.logger import LoggingAdapter

matplotlib.use("Agg")

logger = logging.getLogger(__name__)
log = LoggingAdapter(logger)


def plot_dependency_graph(
    file_path: str, dependency_client: DependencyParser, object_filter: List[str] = []
) -> None:
    """
    Plot a given dependency graph.

    Plot either the full graph or parts of the graph.
    When plotting parts of the graph, show all objects that a given object depends on and objects that depend on the given object.

    file_path: str - Path where the plot will be stored
    dependency_client: DependencyParser - parser object containing the dependency graph
    object_filter: List[str] - show dependencies only for given full object names ('<schema>.<name>'). If an empty list is supplied, plot the complete graph.
    """
    if object_filter:
        dependency_client.filter_graph_by_object_names(object_filter, "plot")
    dependency_graph = dependency_client._dependency_graph

    pos = nx.shell_layout(dependency_graph.reverse())
    # nx.draw_networkx_nodes(dependency_graph, pos, node_size=300)
    nx.draw_networkx_edges(dependency_graph.reverse(), pos, edge_color=".6")
    labels = {
        s: s.full_name.replace(".", ".\n") for s in dependency_graph.reverse().nodes()
    }
    nx.draw_networkx_labels(dependency_graph.reverse(), pos, labels=labels, font_size=6)

    log.info(f"SAVE graph as [ '{file_path}' ]")
    matplotlib.pyplot.savefig(file_path)
