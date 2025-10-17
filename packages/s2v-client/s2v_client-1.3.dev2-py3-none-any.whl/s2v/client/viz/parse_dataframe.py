"""
Author: Mohit Mayank

Parse network data from list of dicts into visdcc format
"""


def compute_scaling_vars_for_numerical_cols(data_list):
    """Identify and scale numerical cols"""
    if not data_list:
        return {}

    # identify numerical cols by checking the type of the first item's values
    numeric_cols = [k for k, v in data_list[0].items() if isinstance(v, int | float)]

    scaling_vars = {}
    for col in numeric_cols:
        # Ensure all items have the key and it's numeric before trying to get min/max
        values = [d[col] for d in data_list if col in d and isinstance(d.get(col), int | float)]
        if values:
            minn, maxx = min(values), max(values)
            scaling_vars[col] = {"min": minn, "max": maxx}
    return scaling_vars


def _create_nodes(edge_list, node_list):
    """Helper to create nodes from a node list or infer them from an edge list."""
    if node_list is None:
        all_node_ids = set()
        for edge in edge_list:
            all_node_ids.add(edge["from"])
            all_node_ids.add(edge["to"])
        return [
            {
                "id": node_name,
                "label": node_name,
                "title": node_name,
                "shape": "dot",
                "size": 7,
            }
            for node_name in all_node_ids
        ]

    nodes = []
    for node in node_list:
        node["id"] = str(node["id"])
        if "title" not in node:
            node["title"] = node["id"]
        if "node_image_url" not in node:
            nodes.append({**node, **{"label": node["title"], "shape": "dot", "size": 7}})
        else:
            image_settings = {"unselected": node["node_image_url"]}
            if "selected_node_image_url" in node:
                image_settings["selected"] = node["selected_node_image_url"]
            nodes.append(
                {
                    **node,
                    **{
                        "label": node["title"],
                        "shape": "circularImage",
                        "image": image_settings,
                        "size": 20,
                    },
                }
            )
    return nodes


def parse_dataframe(edge_list, node_list=None):
    """Parse the network data into visdcc format

    Parameters
    -------------
    edge_list: list of dicts
            The network edge data. Each dict must have 'from' and 'to' keys.

    node_list: list of dicts (optional)
            The network node data. Each dict must have 'id' key.
    """
    # Data checks
    if not all("from" in edge and "to" in edge for edge in edge_list):
        msg = "Each edge in edge_list must have 'from' and 'to' keys."
        raise ValueError(msg)
    if node_list is not None:
        if not all("id" in node for node in node_list):
            msg = "Each node in node_list must have an 'id' key."
            raise ValueError(msg)

    # Convert 'from' and 'to' in edges to string
    for edge in edge_list:
        edge["from"] = str(edge["from"])
        edge["to"] = str(edge["to"])

    # Scaling numerical cols in nodes and edge
    scaling_vars = {"node": None, "edge": None}
    if node_list is not None:
        scaling_vars["node"] = compute_scaling_vars_for_numerical_cols(node_list)
    scaling_vars["edge"] = compute_scaling_vars_for_numerical_cols(edge_list)

    # create node list
    nodes = _create_nodes(edge_list, node_list)

    # create edges from list
    edges = [{**row, **{"id": row["from"] + "__" + row["to"], "color": {"color": "#97C2FC"}}} for row in edge_list]

    return {"nodes": nodes, "edges": edges}, scaling_vars
