import pytest

from jenskipper import digraph
from jenskipper.exceptions import CyclicDependency


def test_topo_sort():
    # 1   2
    #  \ /
    #   3
    graph = digraph.DirectedGraph()
    graph.add_edges_list((1, 3), (2, 3))
    assert digraph.topo_sort(graph) == [2, 1, 3]

    # 1   2
    #  \ /
    #   3 5
    #   |/
    #   4
    graph = digraph.DirectedGraph()
    graph.add_edges_list((1, 3), (2, 3), (3, 4), (5, 4))
    assert digraph.topo_sort(graph) == [5, 2, 1, 3, 4]


def test_split_connected_graphs():
    # 1 - 2 - 3
    # 4 - 5 - 6
    graph = digraph.DirectedGraph()
    graph.add_edges_list((1, 2), (2, 3), (4, 5), (5, 6))
    a, b = digraph.split_connected_graphs(graph)
    assert set(a.nodes.keys()) == {1, 2, 3}
    assert set(b.nodes.keys()) == {4, 5, 6}


def test_topo_sort_cyclic_dependency():
    graph = digraph.DirectedGraph()
    graph.add_edges_list((1, 3), (2, 3), (3, 1))
    with pytest.raises(CyclicDependency) as excinfo:
        digraph.topo_sort(graph)
    assert list(excinfo.value.nodes) == [1, 3]


def test_remove_node():
    graph = digraph.DirectedGraph()
    graph.add_edges_list((1, 3), (2, 3))
    graph.remove_node(2)
    assert set(graph.iter_edges()) == set([(1, 3)])
    assert set(graph.nodes) == set((1, 3))


def test_walk_edges_from_simple_graph():
    # 1 - 2 - 3
    graph = digraph.DirectedGraph()
    edges = [(1, 2), (2, 3)]
    graph.add_edges_list(*edges)
    for start_node in range(1, 4):
        walked_edges = list(graph.walk_edges_from(start_node))
        assert len(walked_edges) == 2
        assert set(walked_edges) == set(edges)


def test_walk_edges_from_disconnected_graphs():
    # 1 - 2 - 3
    # 4 - 5 - 6
    graph = digraph.DirectedGraph()
    edges_a = [(1, 2), (2, 3)]
    edges_b = [(4, 5), (5, 6)]
    graph.add_edges_list(*(edges_a + edges_b))
    for start_node in range(1, 4):
        walked_edges = list(graph.walk_edges_from(start_node))
        assert len(walked_edges) == 2
        assert set(walked_edges) == set(edges_a)
    for start_node in range(4, 7):
        walked_edges = list(graph.walk_edges_from(start_node))
        assert len(walked_edges) == 2
        assert set(graph.walk_edges_from(start_node)) == set(edges_b)


def test_walk_edges_from_complex_graphs():
    # 1   2
    #  \ /
    #   3 5
    #   |/
    #   4
    graph = digraph.DirectedGraph()
    edges = [(1, 3), (2, 3), (3, 4), (5, 4)]
    graph.add_edges_list(*edges)
    for start_node in range(1, 6):
        walked_edges = list(graph.walk_edges_from(start_node))
        assert len(walked_edges) == 4
        assert set(walked_edges) == set(edges)


def test_walk_edges_from_loop_graph():
    #      1
    #     / \
    #    2 - 3
    graph = digraph.DirectedGraph()
    edges = [(1, 2), (2, 3), (3, 1)]
    graph.add_edges_list(*edges)
    for start_node in range(1, 4):
        walked_edges = list(graph.walk_edges_from(start_node))
        assert len(walked_edges) == 3
        assert set(walked_edges) == set(edges)


def test_format():
    # 1   2
    #  \ /
    #   3 5
    #   |/
    #   4
    graph = digraph.DirectedGraph()
    edges = [(1, 3), (2, 3), (3, 4), (5, 4)]
    graph.add_edges_list(*edges)
    assert graph.format().splitlines() == [
        '1 > 3 > 4',
        '2 > 3',
        '5 > 4',
    ]


def test_format_quoted():
    graph = digraph.DirectedGraph()
    graph.add_edge('foo bar', 'baz')
    assert graph.format() == "'foo bar' > baz"


def test_format_many_on_one():
    #   1
    #  / \
    # 2   3
    graph = digraph.DirectedGraph()
    edges = [(1, 2), (1, 3)]
    graph.add_edges_list(*edges)
    assert graph.format().splitlines() == [
        '1 > 2',
        '1 > 3',
    ]


def test_format_edges_reprs():
    # 1 - 2 - 3
    graph = digraph.DirectedGraph()
    edges = [(1, 2), (2, 3, ' |> ')]
    graph.add_edges_list(*edges)
    assert graph.format().splitlines() == [
        '1 > 2 |> 3',
    ]


def test_parse():
    lines = [
        '1 > 3 > 4',
        '2 > 3',
        '5 > 4',
    ]
    graph = digraph.DirectedGraph.parse('\n'.join(lines))
    edges = set(graph.iter_edges())
    assert edges == {
        ('1', '3'),
        ('2', '3'),
        ('3', '4'),
        ('5', '4'),
    }


def test_parse_quoted():
    graph = digraph.DirectedGraph.parse("'foo bar' !> baz")
    edges = list(graph.iter_edges(with_reprs=True))
    assert edges == [('foo bar', 'baz', '!>')]
