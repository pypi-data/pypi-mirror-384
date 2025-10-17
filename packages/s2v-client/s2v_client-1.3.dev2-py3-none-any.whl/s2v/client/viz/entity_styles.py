from enum import Enum

DEFAULT_EDGE_COLOR = "#97C2FC"
HIGHLIGHTED_EDGE_COLOR = "#676767"


class EntityType(Enum):
    HUB = "hub"
    LNK = "link"
    NHL = "non_historized_link"
    # Internal type - highlight on condition
    LNK_WITH_2_CONNECTIONS = "link_with_2_connections"


# Default image
unselected_node_image_url = {
    EntityType.HUB: "https://visual4s2v.blob.core.windows.net/icons/HUB_green_opacity_75.svg",
    EntityType.LNK: "https://visual4s2v.blob.core.windows.net/icons/LINK_gray_opacity_70.svg",
    EntityType.NHL: "https://visual4s2v.blob.core.windows.net/icons/LINK_gray_opacity_70.svg",
    EntityType.LNK_WITH_2_CONNECTIONS: "https://visual4s2v.blob.core.windows.net/icons/LINK_yellow_opacity_100.svg",
}

# Can be ignored if not needed
selected_node_image_url = {
    EntityType.HUB: "https://visual4s2v.blob.core.windows.net/icons/HUB_green_opacity_100.svg",
    EntityType.LNK: "https://visual4s2v.blob.core.windows.net/icons/LINK_gray_opacity_100.svg",
    EntityType.NHL: "https://visual4s2v.blob.core.windows.net/icons/LINK_gray_opacity_100.svg",
    EntityType.LNK_WITH_2_CONNECTIONS: "https://visual4s2v.blob.core.windows.net/icons/LINK_yellow_opacity_100.svg",
}

# Used for transparency
transparent_node_image_url = {
    EntityType.HUB: "https://visual4s2v.blob.core.windows.net/icons/HUB_green_opacity_30.svg",
    EntityType.LNK: "https://visual4s2v.blob.core.windows.net/icons/LINK_gray_opacity_30.svg",
    EntityType.NHL: "https://visual4s2v.blob.core.windows.net/icons/LINK_gray_opacity_30.svg",
    EntityType.LNK_WITH_2_CONNECTIONS: "https://visual4s2v.blob.core.windows.net/icons/LINK_yellow_opacity_30.svg",
}
