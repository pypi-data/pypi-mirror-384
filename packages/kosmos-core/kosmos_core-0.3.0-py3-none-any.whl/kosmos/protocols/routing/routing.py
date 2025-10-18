from abc import ABC

from kosmos.protocols.config.protocol import RoutingProtocolConfig
from kosmos.protocols.protocol import Protocol
from kosmos.topology.link import Link, OpticalLink
from kosmos.topology.net import Network
from kosmos.topology.node import Node


class RoutingProtocol(Protocol, ABC):
    """Routing protocol."""

    def __init__(
        self, config: RoutingProtocolConfig, network: Network, source_node: Node, target_node: Node
    ) -> None:
        """Initialize the routing protocol.

        Args:
            config (RoutingProtocolConfig): Routing protocol configuration.
            network (Network): The network topology.
            source_node (Node): The source node.
            target_node (Node): The target node.

        """
        super().__init__(config, network)
        self.config = config

        self.source_node = source_node
        self.target_node = target_node

    def _link_cost(self, link: Link) -> float:
        """Compute the cost of a link.

        Returns:
            float: The link cost.

        """
        if self.config.cost_function == "distance":
            return self._link_distance(link)
        return link.weight

    @staticmethod
    def _link_distance(link: Link) -> float:
        """Compute the distance of a link.

        Returns:
            float: The link distance.

        """
        if not isinstance(link, OpticalLink):
            msg = "Distance cost function is only supported for optical links."
            raise TypeError(msg)
        return link.distance
