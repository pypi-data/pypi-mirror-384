from collections.abc import Iterable
from dataclasses import dataclass, field

from kosmos.topology.link import Link, LinkId
from kosmos.topology.node import Node, NodeId
from kosmos.topology.typing import LinkReference, NodeReference


@dataclass
class Network:
    """Network that stores nodes and links."""

    _nodes: dict[NodeId, Node] = field(default_factory=dict)
    _links: dict[LinkId, Link] = field(default_factory=dict)
    _node_links: dict[NodeId, list[Link]] = field(default_factory=dict)

    def add_node(self, node: Node) -> None:
        """Add a node to the network.

        Args:
            node (Node): Node instance to insert.

        """
        if node.id in self._nodes:
            msg = f"Node '{node.id.value}' already exists."
            raise ValueError(msg)
        self._nodes[node.id] = node
        self._node_links.setdefault(node.id, [])

    def add_link(self, link: Link) -> None:
        """Add a link to the network.

        Both endpoints of the link must be present in the network.

        Args:
            link (Link): Link instance to insert.

        """
        if link.id in self._links:
            msg = f"Link '{link.id}' already exists."
            raise ValueError(msg)

        missing = [nid for nid in (link.src.id, link.dst.id) if nid not in self._nodes]
        if missing:
            if len(missing) == 1:
                msg = f"Endpoint '{missing[0]}' is not present in the network."
            else:
                ids = ", ".join(f"'{nid}'" for nid in missing)
                msg = f"Endpoints {ids} are not present in the network."
            raise ValueError(msg)

        self._node_links.setdefault(link.src.id, []).append(link)
        self._node_links.setdefault(link.dst.id, []).append(link)

        self._links[link.id] = link

    def get_node(self, node_id: NodeId | str) -> Node | None:
        """Node by id.

        Args:
            node_id (NodeId | str): Identifier of the node.

        Returns:
            Node | None: The node if present, else None.

        """
        if isinstance(node_id, str):
            return self._nodes.get(NodeId(node_id))
        return self._nodes.get(node_id)

    def get_link(self, link_id: LinkId | str) -> Link | None:
        """Link by id.

        Args:
            link_id (LinkId | str): Identifier of the link.

        Returns:
            Link | None: The link if present, else None.

        """
        if isinstance(link_id, str):
            return self._links.get(LinkId(link_id))
        return self._links.get(link_id)

    def nodes(self) -> Iterable[Node]:
        """Iterate over all nodes.

        Returns:
            Iterable[Node]: Iterator over nodes.

        """
        return self._nodes.values()

    def links(self) -> Iterable[Link]:
        """Iterate over all links.

        Returns:
            Iterable[Link]: Iterator over links.

        """
        return self._links.values()

    def outgoing_links(self, node: NodeReference) -> Iterable[Link]:
        """Outgoing links of a node.

        Args:
            node (NodeReference): The node or its id.

        Returns:
            Iterable[Link]: Outgoing links of the node.

        """
        node_id = self._get_valid_node_id(node)
        return tuple(self._node_links.get(node_id, ()))

    def incoming_links(self, node: NodeReference) -> Iterable[Link]:
        """Incoming links of a node.

        Args:
            node (NodeReference): The node or its id.

        Returns:
            Iterable[Link]: Incoming links of the node.

        """
        node_id = self._get_valid_node_id(node)
        return tuple(self._node_links.get(node_id, ()))

    def validate_node(self, node: NodeReference) -> Node:
        """Get the node for a node reference if it is valid, else raise.

        Args:
            node (NodeReference): The node or its id.

        Returns:
            Node: The valid node.

        """
        node_id = self._get_valid_node_id(node)
        return self._nodes.get(node_id)

    def validate_link(self, link: LinkReference) -> Link:
        """Get the link for a link reference if it is valid, else raise.

        Args:
            link (LinkReference): The link or its id.

        Returns:
            Link: The valid link.

        """
        link_id = self._get_valid_link_id(link)
        return self._links.get(link_id)

    def _get_valid_node_id(self, node: NodeReference) -> NodeId:
        """Get the NodeId for a node reference if the node is present in the network, else raise.

        Args:
            node (NodeReference): The node or its id.

        Returns:
            NodeId: The node id.

        """
        if isinstance(node, Node) and node not in self.nodes():
            msg = f"Node {node} with id '{node.id}' is not present in the network."
            raise ValueError(msg)

        node_id = (
            node.id if isinstance(node, Node) else NodeId(node) if isinstance(node, str) else node
        )

        if node_id not in self._nodes:
            msg = f"Node with id '{node_id}' is not present in the network."
            raise ValueError(msg)

        return node_id

    def _get_valid_link_id(self, link: LinkReference) -> LinkId:
        """Get the LinkId for a link reference if the link is present in the network, else raise.

        Args:
            link (LinkReference): The link or its id.

        Returns:
            LinkId: The link id.

        """
        if isinstance(link, Link) and link not in self.links():
            msg = f"Link {link} with id '{link.id}' is not present in the network."
            raise ValueError(msg)

        link_id = (
            link.id if isinstance(link, Link) else LinkId(link) if isinstance(link, str) else link
        )

        if link_id not in self._links:
            msg = f"Link with id '{link_id}' is not present in the network."
            raise ValueError(msg)

        return link_id
