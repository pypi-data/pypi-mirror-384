import logging
from typing import Any

from s2v.client.viz.entity_styles import EntityType, selected_node_image_url, unselected_node_image_url

logger = logging.getLogger(__name__)


def get_entity_type(entity_type_str: str | None) -> EntityType | None:
    try:
        return EntityType(entity_type_str)
    except ValueError:
        return None


connected_entities_field = {EntityType.LNK: "connected_hubs", EntityType.NHL: "connected_hubs"}


class YAMLModelParser:
    """Parser for building Jaal graph representation from yaml-defined data vault model."""

    def __init__(self):
        self.nodes = []
        self.edges = []

    def parse_entity(self, data: dict[str, Any]) -> None:
        entity_name = data.get("name")
        if not entity_name:
            return

        entity_type = get_entity_type(data.get("entity_type"))
        if not entity_type or entity_type not in [EntityType.HUB, EntityType.LNK, EntityType.NHL]:
            return

        # Get connected hubs in case it's a link
        connected_hubs = data.get("connected_hubs", [])

        if len(connected_hubs) == 2:  # noqa: PLR2004
            entity_type = EntityType.LNK_WITH_2_CONNECTIONS

        node = {
            "id": entity_name,
            "object_type": entity_type.value,
            "node_image_url": unselected_node_image_url[entity_type],
            "selected_node_image_url": selected_node_image_url[entity_type],
            # Custom values for node sizing
            "make_hubs_larger": 2 if entity_type == EntityType.HUB else 1,
            "make_links_larger": 1 if entity_type == EntityType.HUB else 2,
        }
        self.nodes.append(node)

        # Add edges in case it's a link
        for hub in connected_hubs:
            # Connected hubs are defined by a single key-value pair
            if not isinstance(hub, dict) or len(hub) != 1:
                logger.error(
                    "Invalid format for connected hub in entity '%s'. "
                    "The hub must be defined as a single key-value pair 'alias: name'.",
                    entity_name,
                )
                continue

            hub_alias = next(iter(hub.keys()))
            hub_name = hub[hub_alias]

            self.edges.append({"from": entity_name, "to": hub_name, "title": hub_alias})
