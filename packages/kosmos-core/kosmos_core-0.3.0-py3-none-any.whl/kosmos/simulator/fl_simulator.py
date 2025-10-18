from collections.abc import Iterator

from kosmos.ml.config.factories.model import VQCConfig
from kosmos.ml.config.sl_train import FLTrainConfig
from kosmos.ml.fl.fl_manager import FLManager
from kosmos.ml.sl_result import SLTestIterationResult, SLTrainIterationResult
from kosmos.protocols.config.protocol import RoutingProtocolConfig
from kosmos.protocols.routing.dijkstra_routing import DijkstraRoutingProtocol
from kosmos.protocols.routing.path import Path
from kosmos.protocols.status import ProtocolStatus
from kosmos.simulator.simulator import Simulator
from kosmos.topology.link import LinkType
from kosmos.topology.net import Network
from kosmos.topology.node import Node, QuantumNode
from kosmos.topology.typing import NodeReference


class FLSimulator(Simulator):
    """Federated learning simulator."""

    def __init__(
        self,
        network: Network,
        train_config: FLTrainConfig,
        client_nodes: list[NodeReference],
        server_node: NodeReference,
        seed: int = 1,
    ) -> None:
        """Initialize the simulator.

        Args:
            network (Network): The network topology.
            train_config (FLTrainConfig): The federated learning training configuration.
            client_nodes (list[NodeReference]): The node references of the clients.
            server_node (NodeReference): The node reference of the server.
            seed (int): The seed for the random number generator. Defaults to 1.

        """
        super().__init__(network, seed)

        self.train_config = train_config

        self.client_nodes = [self.network.validate_node(node_ref) for node_ref in client_nodes]
        self.server_node = self.network.validate_node(server_node)
        self._validate_nodes()

        self.manager = FLManager(self.train_config, self.client_nodes, self.server_node)

    def _validate_nodes(self) -> None:
        """Validate the client and server nodes."""
        model_config = self.train_config.model_config

        if len(self.client_nodes) == 0:
            msg = "There must be at least one client node."
            raise ValueError(msg)

        if isinstance(model_config, VQCConfig):  # Quantum
            dataset = self.train_config.dataset
            encoding = model_config.encoding_config.get_instance(
                dataset.input_dimension, dataset.output_dim
            )
            min_num_qubits = encoding.num_qubits

            for node in [*self.client_nodes, self.server_node]:
                if not isinstance(node, QuantumNode):
                    msg = f"Node {node.id} is not a quantum node."
                    raise TypeError(msg)

                if node.num_qubits < min_num_qubits:
                    msg = (
                        f"Node {node.id} has {node.num_qubits} qubits, "
                        f"but at least {min_num_qubits} qubits are required."
                    )
                    raise ValueError(msg)

        for client_node in self.client_nodes:
            if self._get_path_to_server(client_node) is None:
                msg = (
                    f"No path found from client node {client_node.id} "
                    f"to server node {self.server_node.id}."
                )
                raise ValueError(msg)

    def _get_path_to_server(self, client_node: Node) -> Path | None:
        """Get the path to the server node from the given client node.

        Args:
            client_node (Node): The client node.

        Returns:
            Path | None: The path to the server node, or None if no path was found.

        """
        routing_config = RoutingProtocolConfig(
            allowed_link_types=[LinkType.CLASSICAL], cost_function="cost"
        )
        routing_protocol = DijkstraRoutingProtocol(
            routing_config, self.network, client_node, self.server_node
        )
        routing_result = routing_protocol.execute()
        if routing_result.status == ProtocolStatus.SUCCESS:
            return routing_result.path
        return None

    def train(self) -> Iterator[SLTrainIterationResult]:
        """Run federated training across all configured rounds.

        Returns:
            Iterator[SLTrainIterationResult]: An iterator yielding one training result per epoch
                                              for all rounds.

        """
        yield from self.manager.train()

    def test(self) -> SLTestIterationResult:
        """Evaluate the global model on the test dataset.

        Returns:
            SLTrainIterationResult: The result of the global model evaluation.

        """
        return self.manager.test()
