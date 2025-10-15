import textwrap
import uuid
from typing import Literal

import networkx as nx
from jinja2 import Template

from .graph_text import get_network_text

__all__ = [
    "get_network_text",
    "nx_graph_to_mermaid",
]

def escape_mermaid_label(text: str) -> str:
    """Simple escape for Mermaid labels"""
    return str(text).replace('"', "'").replace("\n", " ")


def nx_graph_to_mermaid(
    nx_graph: nx.DiGraph,
    direction: Literal["TD", "LR", "BT", "RL"] = "TD",
    fenced: bool = True,
) -> str:
    """
    Convert a NetworkX graph to Mermaid diagram format using Jinja2.

    Parameters:
    - graph_type: 'graph' for undirected, 'digraph' for directed
    - direction: 'TD' (top-down), 'LR' (left-right), 'BT' (bottom-top),
        'RL' (right-left)
    """

    # Mermaid template
    mermaid_template = Template(
        textwrap.dedent("""
        graph {{ direction }}
        {%- for node in nodes %}
            {{ node.id }}[{{ node.label }}]
        {%- endfor %}
        {%- for edge in edges %}
            {{ edge.source }} --> {{ edge.target }}
            {%- if edge.label %}
            {{ edge.source }} -.-> |{{ edge.label }}| {{ edge.target }}
            {%- endif %}
        {%- endfor %}
        """).strip()
    )

    # Prepare data for template
    node_ids = {}
    for node in nx_graph.nodes():
        node_ids[node] = str(uuid.uuid4())[:8]

    def node_label(node) -> str:
        """Further escape double underscores"""
        res = escape_mermaid_label(repr(node)).replace("__", "&lowbar;&lowbar;")
        return '"' + res + '"'

    nodes = []
    for node in nx_graph.nodes():
        nodes.append(
            {
                "id": node_ids[node],
                "label": node_label(node),
            }
        )

    edges = []
    for source, target in nx_graph.edges():
        edges.append(
            {
                "source": node_ids[source],
                "target": node_ids[target],
                "label": "",
            }
        )

    # Render template
    mermaid_code = mermaid_template.render(
        direction=direction,
        nodes=nodes,
        edges=edges,
    )

    if fenced:
        mermaid_code = f"```mermaid\n{mermaid_code}\n```"

    return mermaid_code