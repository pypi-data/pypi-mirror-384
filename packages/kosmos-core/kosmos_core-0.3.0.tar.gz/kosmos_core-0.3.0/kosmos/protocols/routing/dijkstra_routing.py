import heapq
import itertools
import math
from collections import deque

from kosmos.protocols.config.protocol import RoutingProtocolConfig
from kosmos.protocols.protocol_result import RoutingProtocolResult
from kosmos.protocols.routing.path import Path
from kosmos.protocols.routing.routing import RoutingProtocol
from kosmos.protocols.status import ProtocolStatus
from kosmos.topology.link import Link
from kosmos.topology.net import Network
from kosmos.topology.node import Node


class DijkstraRoutingProtocol(RoutingProtocol):
    """Dijkstra routing protocol."""

    def __init__(
        self, config: RoutingProtocolConfig, network: Network, source_node: Node, target_node: Node
    ) -> None:
        """Initialize the Dijkstra routing protocol.

        Args:
            config (RoutingProtocolConfig): Routing protocol configuration.
            network (Network): The network topology.
            source_node (Node): The source node.
            target_node (Node): The target node.

        """
        super().__init__(config, network, source_node, target_node)

        self.source_node = source_node
        self.target_node = target_node

    def execute(self) -> RoutingProtocolResult:
        """Execute the Dijkstra routing protocol.

        Returns:
            RoutingProtocolResult: Result of the routing protocol execution.

        """
        self.status = ProtocolStatus.RUNNING

        visited_nodes = set()

        cost_from_src: dict[Node, float] = dict.fromkeys(self.network.nodes(), math.inf)
        cost_from_src[self.source_node] = 0.0

        # Track predecessor nodes and the link used to reach them
        predecessor: dict[Node, tuple[Node, Link]] = {}

        # Include push_seq for tiebreaking; earlier pushes are preferred if cost is equal
        push_seq = itertools.count()
        heap = [(0.0, next(push_seq), self.source_node)]

        while heap:
            current_cost_from_src, _, current_node = heapq.heappop(heap)

            if current_cost_from_src > cost_from_src[current_node]:
                continue

            if current_node == self.target_node:
                break

            visited_nodes.add(current_node)

            for link in self.network.outgoing_links(current_node):
                if link.type not in self.config.allowed_link_types:
                    continue

                neighbor = link.dst if link.src == current_node else link.src

                if neighbor in visited_nodes:
                    continue

                tentative_cost = current_cost_from_src + self._link_cost(link)
                if tentative_cost < cost_from_src[neighbor]:
                    cost_from_src[neighbor] = tentative_cost
                    predecessor[neighbor] = (current_node, link)
                    heapq.heappush(heap, (tentative_cost, next(push_seq), neighbor))

        if self.target_node not in predecessor and self.target_node != self.source_node:
            # No path found
            self.status = ProtocolStatus.FAILED
            return RoutingProtocolResult(
                status=self.status, path=None, total_cost=None, total_distance=None
            )

        # Build the path by following predecessors
        node_path: deque[Node] = deque()
        link_path: deque[Link] = deque()
        total_cost = 0.0
        total_distance = 0.0
        current = self.target_node

        while current != self.source_node:
            prev_node, used_link = predecessor[current]
            node_path.appendleft(current)
            link_path.appendleft(used_link)
            total_cost += self._link_cost(used_link)
            total_distance += self._link_distance(used_link)
            current = prev_node
        node_path.appendleft(self.source_node)

        result = RoutingProtocolResult(
            status=ProtocolStatus.RUNNING,
            path=Path(list(node_path), list(link_path)),
            total_cost=total_cost,
            total_distance=total_distance,
        )
        self.status = ProtocolStatus.SUCCESS
        result.status = self.status
        return result
