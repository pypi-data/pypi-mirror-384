"""
Author: Mohit Mayank

Main class for Jaal network visualization dashboard
"""

import copy
import logging

import dash
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

from s2v.client.viz.entity_styles import (
    DEFAULT_EDGE_COLOR,
    HIGHLIGHTED_EDGE_COLOR,
    EntityType,
    transparent_node_image_url,
    unselected_node_image_url,
)
from s2v.client.viz.layout import (
    DEFAULT_BORDER_SIZE,
    DEFAULT_EDGE_SIZE,
    DEFAULT_NODE_SIZE,
    create_color_legend,
    get_app_layout,
    get_distinct_colors,
)
from s2v.client.viz.parse_dataframe import parse_dataframe

_LOGGER = logging.getLogger(__name__)


# class
class Jaal:
    """The main visualization class"""

    def __init__(self, edge_list, node_list=None):
        """
        Parameters
        -------------
        edge_list: list of dicts
            The network edge data

        node_list: list of dicts (optional)
            The network node data
        """
        _LOGGER.debug("Parsing the data...")
        self.data, self.scaling_vars = parse_dataframe(edge_list, node_list)
        self.filtered_data = self.data.copy()
        self.original_data = self._set_default_styles(copy.deepcopy(self.data))
        self.node_value_color_mapping = {}
        self.edge_value_color_mapping = {}
        _LOGGER.debug("Done")

    def _callback_search_graph(self, graph_data, search_text):
        """Hide the nodes unrelated to search quiery"""
        nodes = graph_data["nodes"]
        edges = graph_data["edges"]
        matching_nodes = set()
        visible_nodes = set()
        node_neighborhood = {}

        # Find nodes matching the query
        for node in nodes:
            if search_text.lower().strip() == node["label"].lower().strip():
                matching_nodes.add(node["id"])
                if node["object_type"] == "HUB":
                    node_neighborhood[node["id"]] = 2
                else:
                    node_neighborhood[node["id"]] = 1

        # Function to find neighbors up to the specified neighborhood size
        def find_neighbors(current_nodes, current_neighborhood, max_neighborhood):
            if current_neighborhood > max_neighborhood:
                return
            new_neighbors = set()
            for edge in edges:
                if edge["from"] in current_nodes:
                    new_neighbors.add(edge["to"])
                if edge["to"] in current_nodes:
                    new_neighbors.add(edge["from"])
            visible_nodes.update(new_neighbors)
            find_neighbors(new_neighbors, current_neighborhood + 1, max_neighborhood)

        # Find neighbors for each matching node
        for node_id in matching_nodes:
            if node_id in node_neighborhood:
                find_neighbors({node_id}, 1, node_neighborhood[node_id])
            else:
                _LOGGER.warning("Node %s not found in node_neighborhood", node_id)

        visible_nodes.update(matching_nodes)
        # Change nodes style
        for node in nodes:
            if node["id"] in matching_nodes:
                node["color"] = {"border": HIGHLIGHTED_EDGE_COLOR}
                node["borderWidth"] = 4
                # Highlight edges connected to the matching nodes
                for edge in edges:
                    if edge["from"] == node["id"] or edge["to"] == node["id"]:
                        edge["color"] = {"color": HIGHLIGHTED_EDGE_COLOR}
                        edge["width"] = 3
            else:
                # Hide nodes irrelevant to the search
                # node['hidden'] = node['id'] not in visible_nodes
                node_type = EntityType(node["object_type"])
                node["image"]["unselected"] = transparent_node_image_url[node_type]

        graph_data["nodes"] = nodes
        return graph_data

    def _set_default_styles(self, graph_data):
        """Set the graph style to the defaults."""
        # print("Resetting to original data")
        # original_graph_data = copy.deepcopy(self.original_data)
        # Ensure all nodes and edges are visible and reset their styles
        for node in graph_data["nodes"]:
            # node['hidden'] = False
            node_type = EntityType(node["object_type"])
            node["image"]["unselected"] = unselected_node_image_url[node_type]

            # node['color'] = {'background': DEFAULT_NODE_COLOR}
            node["borderWidth"] = DEFAULT_BORDER_SIZE

            node_type = EntityType(node["object_type"])
            node["image"]["unselected"] = unselected_node_image_url[node_type]

        for edge in graph_data["edges"]:
            edge["hidden"] = False
            edge["color"] = {"color": DEFAULT_EDGE_COLOR}
            edge["width"] = DEFAULT_EDGE_SIZE
        return graph_data

    def _callback_search_connections(self, graph_data, search_from, search_to, search_distance):
        """Find paths between nodes and hide unrelated nodes and hubs."""
        nodes = graph_data["nodes"]
        edges = graph_data["edges"]
        visible_nodes = set()
        matching_paths = []

        if not search_from or not search_to:
            return graph_data

        # Find the IDs of the from and to nodes
        from_nodes = {node["id"] for node in nodes if search_from.lower() == node["label"].lower()}
        to_nodes = {node["id"] for node in nodes if search_to.lower() == node["label"].lower()}

        # Function to find paths within a given distance
        def find_paths(current_path, current_distance, max_distance):
            if current_distance > max_distance:
                return
            last_node = current_path[-1]
            if last_node in to_nodes:
                matching_paths.append(current_path)
                return
            for edge in edges:
                if edge["from"] == last_node and edge["to"] not in current_path:
                    find_paths([*current_path, edge["to"]], current_distance + 1, max_distance)
                elif edge["to"] == last_node and edge["from"] not in current_path:
                    find_paths([*current_path, edge["from"]], current_distance + 1, max_distance)

        # Determine the maximum distance
        if search_distance == "Any":
            max_distance = float("inf")
        else:
            max_distance = int(search_distance)

        # Find paths from each from_node
        for from_node in from_nodes:
            find_paths([from_node], 0, max_distance)

        # Collect visible nodes from matching paths
        for path in matching_paths:
            visible_nodes.update(path)

        # Hide nodes that are not part of any matching path
        for node in nodes:
            if node["id"] not in visible_nodes:
                node_type = EntityType(node["object_type"])
                node["image"]["unselected"] = transparent_node_image_url[node_type]
            # node['hidden'] = node['id'] not in visible_nodes

        graph_data["nodes"] = nodes
        return graph_data

    def _callback_show_nodes_with_no_edges(self, graph_data, checked):
        """Show only nodes with no connections if checked, otherwise show the whole graph."""
        nodes = graph_data["nodes"]
        edges = graph_data["edges"]

        if checked:
            connected_nodes = set()
            # Find all nodes that are connected
            for edge in edges:
                connected_nodes.add(edge["from"])
                connected_nodes.add(edge["to"])

            # Hide nodes that are connected
            for node in nodes:
                if node["id"] not in connected_nodes:
                    node_type = EntityType(node["object_type"])
                    node["image"]["unselected"] = transparent_node_image_url[node_type]
                # node['hidden'] = node['id'] in connected_nodes
        else:
            # Show all nodes
            for node in nodes:
                # node['hidden'] = False
                node["image"]["unselected"] = unselected_node_image_url[node_type]

        graph_data["nodes"] = nodes
        return graph_data

    def _callback_size_nodes(self, graph_data, size_nodes_value):
        # size option is None, revert back all changes
        if size_nodes_value == "None":
            # revert to default size
            for node in self.data["nodes"]:
                node["size"] = DEFAULT_NODE_SIZE
        else:
            _LOGGER.debug("Modifying node size using %s", size_nodes_value)
            # fetch the scaling value
            minn = self.scaling_vars["node"][size_nodes_value]["min"]
            maxx = self.scaling_vars["node"][size_nodes_value]["max"]

            # define the scaling function
            def scale_val(x):
                return 10 * (x - minn) / (maxx - minn)

            # set size after scaling
            for node in self.data["nodes"]:
                node["size"] = DEFAULT_NODE_SIZE + scale_val(node[size_nodes_value])
        # filter the data currently shown
        filtered_nodes = [x["id"] for x in self.filtered_data["nodes"]]
        self.filtered_data["nodes"] = [x for x in self.data["nodes"] if x["id"] in filtered_nodes]
        graph_data = self.filtered_data
        return graph_data

    def _callback_color_edges(self, graph_data, color_edges_value):
        value_color_mapping = {}
        # color option is None, revert back all changes
        if color_edges_value == "None":
            # revert to default color
            for edge in self.data["edges"]:
                edge["color"]["color"] = DEFAULT_EDGE_COLOR
        else:
            _LOGGER.debug("inside color edge %s", color_edges_value)
            unique_values = list({edge[color_edges_value] for edge in self.data["edges"]})
            colors = get_distinct_colors(len(unique_values))
            value_color_mapping = dict(zip(unique_values, colors, strict=False))
            for edge in self.data["edges"]:
                edge["color"]["color"] = value_color_mapping[edge[color_edges_value]]
        # filter the data currently shown
        filtered_edges = [x["id"] for x in self.filtered_data["edges"]]
        self.filtered_data["edges"] = [x for x in self.data["edges"] if x["id"] in filtered_edges]
        graph_data = self.filtered_data
        return graph_data, value_color_mapping

    def _callback_size_edges(self, graph_data, size_edges_value):
        # size option is None, revert back all changes
        if size_edges_value == "None":
            # revert to default size
            for edge in self.data["edges"]:
                edge["width"] = DEFAULT_EDGE_SIZE
        else:
            _LOGGER.debug("Modifying edge size using %s", size_edges_value)
            # fetch the scaling value
            minn = self.scaling_vars["edge"][size_edges_value]["min"]
            maxx = self.scaling_vars["edge"][size_edges_value]["max"]

            # define the scaling function
            def scale_val(x):
                return 10 * (x - minn) / (maxx - minn)

            # set the size after scaling
            for edge in self.data["edges"]:
                edge["width"] = DEFAULT_EDGE_SIZE + scale_val(edge[size_edges_value])
        # filter the data currently shown
        filtered_edges = [x["id"] for x in self.filtered_data["edges"]]
        self.filtered_data["edges"] = [x for x in self.data["edges"] if x["id"] in filtered_edges]
        graph_data = self.filtered_data
        return graph_data

    def get_color_popover_legend_children(self, node_value_color_mapping=None, edge_value_color_mapping=None):
        """Get the popover legends for node and edge based on the color setting"""
        # var
        if edge_value_color_mapping is None:
            edge_value_color_mapping = {}
        if node_value_color_mapping is None:
            node_value_color_mapping = {}
        popover_legend_children = []

        # common function
        def create_legends_for(title="Node", legends=None):
            # add title
            if legends is None:
                legends = {}
            _popover_legend_children = [dbc.PopoverHeader(f"{title} legends")]
            # add values if present
            if len(legends) > 0:
                for key, value in legends.items():
                    _popover_legend_children.append(
                        # dbc.PopoverBody(f"Key: {key}, Value: {value}")
                        create_color_legend(key, value)
                    )
            else:  # otherwise add filler
                _popover_legend_children.append(dbc.PopoverBody(f"no {title.lower()} colored!"))
            return _popover_legend_children

        # add node color legends
        popover_legend_children.extend(create_legends_for("Node", node_value_color_mapping))
        # add edge color legends
        popover_legend_children.extend(create_legends_for("Edge", edge_value_color_mapping))
        return popover_legend_children

    def create(self, directed=False, vis_opts=None, title=None):
        """Create the Jaal app and return it

        Parameter
        ----------
            directed: boolean
                process the graph as directed graph?

            vis_opts: dict
                the visual options to be passed to the dash server (default: None)

        Returns
        -------
            app: dash.Dash
                the Jaal app
        """
        # create the app
        app = dash.dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], title=title)

        # define layout
        app.layout = get_app_layout(  # type: ignore[misc]
            self.data, _color_legends=self.get_color_popover_legend_children(), directed=directed, vis_opts=vis_opts
        )

        # create callbacks to toggle legend popover
        @app.callback(
            Output("color-legend-popup", "is_open"),
            [Input("color-legend-toggle", "n_clicks")],
            [State("color-legend-popup", "is_open")],
        )
        def toggle_popover(n, is_open):
            if n:
                return not is_open
            return is_open

        # create callbacks to toggle hide/show sections - FILTER section
        @app.callback(
            Output("filter-show-toggle", "is_open"),
            [Input("filter-show-toggle-button", "n_clicks")],
            [State("filter-show-toggle", "is_open")],
        )
        def toggle_filter_collapse(n, is_open):
            if n:
                return not is_open
            return is_open

        @app.callback(
            Output("graph", "data"),
            [
                Input("clear_search_button", "n_clicks"),
                Input("clear_size_button", "n_clicks"),
                Input("search_button", "n_clicks"),
                Input("search_connections_button", "n_clicks"),
                Input("nodes_with_no_edges_checkbox", "checked"),
                Input("size_nodes", "value"),
                Input("size_edges", "value"),
            ],
            [
                State("search_graph", "value"),
                State("search_from_graph", "value"),
                State("search_to_graph", "value"),
                State("search_distance", "value"),
                State("graph", "data"),
            ],
        )
        def update_graph(  # noqa: PLR0912, PLR0913
            n_clicks_clear_search,
            n_clicks_clear_size,
            n_clicks_search,
            n_clicks_connections,
            checked,
            size_nodes_value,
            size_edges_value,
            search_text,
            search_from,
            search_to,
            search_distance,
            graph_data,
        ):
            ctx = dash.callback_context  # type: ignore[attr-defined]

            if not ctx.triggered:
                raise PreventUpdate

            input_id = ctx.triggered[0]["prop_id"].split(".")[0]

            # graph_data = copy.deepcopy(self.original_data)

            if input_id in ("clear_search_button", "clear_size_button"):
                if n_clicks_clear_search == 0 and n_clicks_clear_size == 0:
                    raise PreventUpdate
                else:
                    graph_data = self._set_default_styles(copy.deepcopy(self.original_data))

            elif input_id == "search_button":
                if n_clicks_search > 0 and search_text:
                    graph_data = self._callback_search_graph(copy.deepcopy(self.original_data), search_text)
                else:
                    graph_data = copy.deepcopy(self.original_data)

            elif input_id == "search_connections_button":
                if n_clicks_connections is None:
                    raise PreventUpdate
                graph_data = self._callback_search_connections(graph_data, search_from, search_to, search_distance)

            elif input_id == "nodes_with_no_edges_checkbox":
                graph_data = self._callback_show_nodes_with_no_edges(graph_data, checked)

            elif input_id == "size_nodes":
                graph_data = self._callback_size_nodes(copy.deepcopy(self.original_data), size_nodes_value)

            elif input_id == "size_edges":
                graph_data = self._callback_size_edges(copy.deepcopy(self.original_data), size_edges_value)

            else:
                graph_data = self.data

            return copy.deepcopy(graph_data)

        return app

    def plot(self, debug=False, host="127.0.0.1", port=8050, directed=False, vis_opts=None, title=None):
        """Plot the Jaal by first creating the app and then hosting it on default server

        Parameter
        ----------
            debug (boolean)
                run the debug instance of Dash?

            host: string
                ip address on which to run the dash server (default: 127.0.0.1)

            port: string
                port on which to expose the dash server (default: 8050)

            directed (boolean):
                whether the graph is directed or not (default: False)

            vis_opts: dict
                the visual options to be passed to the dash server (default: None)
        """
        # call the create_graph function
        app = self.create(directed=directed, vis_opts=vis_opts, title=title)
        # run the server
        app.run_server(debug=debug, host=host, port=port)
