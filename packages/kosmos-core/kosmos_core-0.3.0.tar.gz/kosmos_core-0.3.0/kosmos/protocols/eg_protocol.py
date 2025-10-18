from kosmos.protocols.config.protocol import EGProtocolConfig
from kosmos.protocols.protocol import Protocol, ProtocolStatus
from kosmos.protocols.protocol_result import EGProtocolResult
from kosmos.quantum_logic.quantum_register_manager import QuantumRegisterManager
from kosmos.topology.net import Network
from kosmos.topology.node import QuantumNode


class EGProtocol(Protocol):
    """Entanglement generation protocol.

    This protocol allocates communication qubits at the source and target nodes,
    then creates entanglement between them based on the quantum link properties.
    """

    def __init__(
        self,
        config: EGProtocolConfig,
        network: Network,
        quantum_manager: QuantumRegisterManager,
        source_node: QuantumNode,
        target_node: QuantumNode,
    ) -> None:
        """Initialize the entanglement generation protocol.

        Args:
            config (EGProtocolConfig): Entanglement generation protocol configuration.
            network (Network): The network topology.
            quantum_manager (QuantumRegisterManager): The quantum register manager.
            source_node (QuantumNode): The source node.
            target_node (QuantumNode): The target node.

        """
        super().__init__(config, network)

        self.quantum_manager = quantum_manager
        self.source_node = source_node
        self.target_node = target_node

    def execute(self) -> EGProtocolResult:
        """Execute the entanglement generation protocol.

        Returns:
            EGProtocolResult: Result of the entanglement generation protocol execution.

        """
        self.status = ProtocolStatus.RUNNING
        return EGProtocolResult(self.status)
