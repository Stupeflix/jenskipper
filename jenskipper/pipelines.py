import six

from . import digraph


GRAPH_EDGES_REPRS = {
    'SUCCESS': ' > ',
    'UNSTABLE': ' ?> ',
    'FAILURE': ' ~> ',
}
JENKINS_LINK_TYPES = {v.strip(): k for k, v in GRAPH_EDGES_REPRS.items()}


def format_pipes_bits(bits):
    """
    Assemble *bits* of pipelines as text.

    *bits* must be a dict of ``(parents_list, upstream_link_type)`` pairs,
    indexed by job name.
    """
    graph = digraph.DirectedGraph()
    for child, (parents, upstream_link_type) in bits.items():
        edges_repr = GRAPH_EDGES_REPRS[upstream_link_type]
        for parent in parents:
            graph.add_edge(parent, child, edges_repr)
    return graph.format()


def parse_pipelines(text):
    """
    Parse the pipelines defined in *text*.
    """
    graph = digraph.DirectedGraph.parse(text)
    ret = {}
    for child, parents in graph.parents.items():
        parents = sorted([six.text_type(p) for p in parents])
        first_parent = parents[0]
        edge = (first_parent, child)
        edge_repr = graph.edges_reprs[edge]
        link_type = JENKINS_LINK_TYPES[edge_repr]
        ret[child] = (parents, link_type)
    return ret
