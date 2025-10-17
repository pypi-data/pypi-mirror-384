import pathlib
from collections import defaultdict
from typing import TypedDict

import yaml

from s2v.client.viz.jaal import Jaal
from s2v.client.viz.yaml_model_parser import YAMLModelParser

DEFAULT_VIZ_OPTS = {
    "height": "800px",
    "interaction": {
        "hover": True,  # Highlight node and its edges on hover
    },
    "physics": {"stabilization": {"iterations": 300}, "barnesHut": {"gravitationalConstant": -3000}},
    "layout": {"improvedLayout": True},
    "edges": {
        "font": {
            "color": "#ff5353",
            "size": 8,
        },
    },
}


class EdgeGroup(TypedDict):
    count: int
    titles: list[str]


def visualize(input_dir: pathlib.Path) -> None:
    model_name = input_dir.name

    parser = YAMLModelParser()

    for file in input_dir.rglob("*.yaml"):
        with file.open() as f:
            data = yaml.safe_load(f)
            parser.parse_entity(data)

    # Remove duplicate nodes
    unique_nodes = []
    seen_node_ids = set()
    for node in parser.nodes:
        if node["id"] not in seen_node_ids:
            unique_nodes.append(node)
            seen_node_ids.add(node["id"])

    # Group duplicate edges, count them, and aggregate titles
    edge_groups: defaultdict[tuple[str, str], EdgeGroup] = defaultdict(lambda: {"count": 0, "titles": []})
    for edge in parser.edges:
        key = (edge["from"], edge["to"])
        edge_groups[key]["count"] += 1
        edge_groups[key]["titles"].append(edge["title"])

    grouped_edges = []
    for (from_node, to_node), data in edge_groups.items():
        grouped_edges.append(
            {"from": from_node, "to": to_node, "count": data["count"], "title": ", ".join(data["titles"])}
        )

    # Initialize Jaal with the data and plot
    jaal = Jaal(edge_list=grouped_edges, node_list=unique_nodes)
    jaal.plot(vis_opts=DEFAULT_VIZ_OPTS, port=8050, title=f"Model {model_name}")
