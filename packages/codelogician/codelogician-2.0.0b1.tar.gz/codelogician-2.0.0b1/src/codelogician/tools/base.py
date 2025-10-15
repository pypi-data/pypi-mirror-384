from __future__ import annotations

from abc import abstractmethod
from collections.abc import Callable
from io import StringIO
from typing import Literal, Self

import joblib
import networkx as nx
import structlog
from rich.console import Console
from rich.tree import Tree

from ..dep_tools.utils import get_network_text, nx_graph_to_mermaid

logger = structlog.get_logger(__name__)

class NodeMixin:
    @property
    @abstractmethod
    def path_key(self) -> str:
        """Primary key for the node. Used for indexing."""
        pass

    @abstractmethod
    def __hash__(self) -> int:
        pass

    @abstractmethod
    def __repr__(self) -> str:
        pass


def nx_graph_from_adjacency_list[Node: NodeMixin](
    nodes: list[Node],
    adjacency_list: dict[str, set[str]],
) -> nx.DiGraph:
    """
    Args:
        - nodes: list of nodes
        - adjacency_list: adjacency list of the graph
            - key: node key (path_key)
            - value: set of node keys that the key node depends on
    Returns:
        - DependencyGraph
    """
    # Check pkey uniqueness
    if len({node.path_key for node in nodes}) != len(nodes):
        raise ValueError("Nodes must have unique path keys")

    def get_node_by_key(key: str) -> Node:
        maybe_node = next((node for node in nodes if node.path_key == key), None)
        if maybe_node is None:
            raise ValueError(f"Node with key {key} not found")
        return maybe_node

    nx_graph = nx.DiGraph()
    for node in nodes:
        nx_graph.add_node(node)

    for src_key, tgt_keys in adjacency_list.items():
        src_node = get_node_by_key(src_key)
        for tgt_key in tgt_keys:
            tgt_node = get_node_by_key(tgt_key)
            nx_graph.add_edge(src_node, tgt_node)

    return nx_graph


class DepGraph[Node: NodeMixin]:
    """
    Dependency graph
    - Edge type: Singleton {}
    - Node and edge meaning:
        - 1. (file | dir, contains)
        - 2. (module | package, import)
        - 3. (symbol, use)
    """

    def __init__(self, nx_graph: nx.DiGraph):
        # Check singleton edge type
        for _src, _tgt, data in nx_graph.edges(data=True):
            if data != {}:
                raise ValueError(f"Edge type must be `{{}}`, but got `{data}`")
        self.nx_graph = nx_graph

    def get_node_by_path(self, path: str) -> Node | None:
        return next((node for node in self.nodes if node.path_key == path), None)

    @property
    def nodes(self) -> list[Node]:
        return list(self.nx_graph.nodes)

    @property
    def is_tree(self) -> bool:
        """Connected and acyclic"""
        return nx.is_tree(self.nx_graph)

    @property
    def is_acyclic(self) -> bool:
        return nx.is_directed_acyclic_graph(self.nx_graph)

    ##########
    # Factory
    ##########

    @classmethod
    def from_adjacency_list(
        cls,
        nodes: list[Node],
        adjacency_list: dict[str, set[str]],
    ) -> DepGraph[Node]:
        nx_graph = nx_graph_from_adjacency_list(nodes, adjacency_list)
        return cls(nx_graph)

    def get_adjacency_list(self) -> dict[str, set[str]]:
        adj = dict(self.nx_graph.adjacency())
        return {
            node.path_key: {tgt.path_key for tgt in tgts} for node, tgts in adj.items()
        }

    ##########
    # Node getters
    ##########
    def get_all_nodes(
        self,
        order: Literal["leaves_to_root", "root_to_leaves"] | None = "leaves_to_root",
    ) -> list[Node]:
        if order in ["root_to_leaves", "leaves_to_root"]:
            topo_sorted_nodes = list(nx.topological_sort(self.nx_graph))
            if order == "root_to_leaves":
                return topo_sorted_nodes
            else:
                return topo_sorted_nodes[::-1]
        else:
            return list(self.nx_graph.nodes)

    def get_successors(self, node: Node) -> list[Node]:
        return list(self.nx_graph.successors(node))

    def get_predecessors(self, node: Node) -> list[Node]:
        return list(self.nx_graph.predecessors(node))

    def get_orphan_nodes(self) -> list[Node]:
        return [
            node
            for node in self.nx_graph
            if not list(self.nx_graph.successors(node))
            and not list(self.nx_graph.predecessors(node))
        ]

    def get_terminal_nodes(self) -> list[Node]:
        return [
            node for node in self.nx_graph if not list(self.nx_graph.successors(node))
        ]

    def get_initial_nodes(self) -> list[Node]:
        return [
            node for node in self.nx_graph if not list(self.nx_graph.predecessors(node))
        ]

    def get_root_node(self) -> Node:
        if not self.is_tree:
            raise ValueError("Graph is not a tree")
        return self.get_initial_nodes()[0]

    def get_descendants(
        self,
        node: Node,
        order: Literal["leaves_to_root", "root_to_leaves"] | None = "leaves_to_root",
    ) -> list[Node]:
        descendants = list(nx.descendants(self.nx_graph, node))
        return (
            [n for n in self.get_all_nodes(order=order) if n in descendants]
            if order in ["root_to_leaves", "leaves_to_root"]
            else descendants
        )

    def get_ancestors(
        self,
        node: Node,
        order: Literal["leaves_to_root", "root_to_leaves"] | None = "leaves_to_root",
    ) -> list[Node]:
        ancestors = list(nx.ancestors(self.nx_graph, node))
        if order in ["root_to_leaves", "leaves_to_root"]:
            if order == "root_to_leaves":
                return ancestors
            else:
                return ancestors[::-1]
        else:
            return ancestors

    ##########
    # Subgraph
    ##########

    def filter_nodes(self, predicate: Callable[[Node], bool]) -> Self:
        """
        Create a new DependencyGraph by removing nodes that satisfy the predicate
        condition.
        """
        # Get nodes to keep (inverse of the predicate)
        nodes_to_keep = [node for node in self.nx_graph.nodes if not predicate(node)]

        # Create subgraph with only the nodes we want to keep
        filtered_nx_graph = self.nx_graph.subgraph(nodes_to_keep).copy()

        return self.__class__(filtered_nx_graph)

    ##########
    # IO
    ##########

    def dump(self, filename: str) -> str:
        nodes = self.nodes
        adj_list = self.get_adjacency_list()
        data = {"nodes": nodes, "adj_list": adj_list}

        return joblib.dump(data, filename)

    @classmethod
    def load(cls, filename: str) -> Self:
        data = joblib.load(filename)
        nodes = data["nodes"]
        adj_list = data["adj_list"]
        return cls.from_adjacency_list(nodes, adj_list)

    ##########
    # Repr
    ##########

    def edges_repr(self) -> str:
        return "\n".join(f"{src!r} --> {tgt!r}" for src, tgt in self.nx_graph.edges())

    def graph_repr(self, method: Literal["rich", "nx"] = "rich") -> str:
        if method == "nx":
            return get_network_text(self, ascii_only=True)
        else:
            adj_list = self.get_adjacency_list()
            nodes = self.nodes

            def pkey_to_repr(pkey: str) -> str:
                node = next((node for node in nodes if node.path_key == pkey), None)
                if node is None:
                    raise ValueError(f"Node with path key {pkey} not found")
                return repr(node)

            adj_repr: dict[str, list[str]] = {
                pkey_to_repr(src): [pkey_to_repr(tgt) for tgt in tgts]
                for src, tgts in adj_list.items()
            }
            # sort by src repr
            adj_repr = dict(sorted(adj_repr.items()))
            # sort by tgt repr
            adj_repr = {src: sorted(tgts) for src, tgts in adj_repr.items()}

            trees = []
            for src, tgts in adj_repr.items():
                tree = Tree(src)
                for tgt in tgts:
                    tree.add(tgt)
                trees.append(tree)

            string_buffer = StringIO()
            console = Console(file=string_buffer, width=80, record=True)
            for tree in trees:
                console.print(tree)
            return console.export_text()

    def _repr_markdown_(self) -> str:
        return nx_graph_to_mermaid(self.nx_graph)