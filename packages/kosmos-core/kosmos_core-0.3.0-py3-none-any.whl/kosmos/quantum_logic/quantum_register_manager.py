import numpy as np

from kosmos.quantum_logic.entanglement_link import EntanglementLink
from kosmos.quantum_logic.quantum_state import QuantumState
from kosmos.quantum_logic.qubit import Qubit, QubitId, QubitType
from kosmos.quantum_logic.typing import QubitReference
from kosmos.topology.net import Network
from kosmos.topology.node import QuantumNode
from kosmos.topology.typing import NodeReference

BELL_PAIR_QUBITS = 2
MIN_FIDELITY_THRESHOLD = 0.25


def _create_bell_state(current_time: int, fidelity: float = 1.0) -> QuantumState:
    """Create a Bell state with given fidelity.

    Args:
        current_time (int): Current time in the simulation.
        fidelity (float): Desired fidelity (0-1). Defaults to 1.0.

    Returns:
        QuantumState: Bell state with specified fidelity.

    """
    if fidelity > 1.0 or fidelity < 0.0:
        msg = "Fidelity must be a float between 0 and 1."
        raise ValueError(msg)

    # Perfect Bell state (|PHI+⟩ = (|00⟩ + |11⟩)/√2)
    perfect_bell = np.zeros((4, 4), dtype=complex)
    perfect_bell[0, 0] = 0.5
    perfect_bell[0, 3] = 0.5
    perfect_bell[3, 0] = 0.5
    perfect_bell[3, 3] = 0.5

    # Maximally mixed state
    mixed = np.eye(4) / 4

    if fidelity > MIN_FIDELITY_THRESHOLD:
        p = (4 * fidelity - 1) / 3
        rho = p * perfect_bell + (1 - p) * mixed
    else:
        rho = mixed

    return QuantumState(rho=rho, fidelity=fidelity, creation_time=current_time)


class QuantumRegisterManager:
    """Manager for quantum logic in the network.

    This manager handles all qubits, entanglements and quantum states in the system.

    """

    def __init__(self, network: Network) -> None:
        """Initialize quantum register manager.

        Args:
            network (Network): The network topology.

        """
        self.network = network
        self.qubits: dict[QubitId, Qubit] = {}
        self.entanglements: dict[frozenset[QubitId], EntanglementLink] = {}
        self.states: dict[frozenset[QubitId], QuantumState] = {}
        self.qubit_to_state_key: dict[QubitId, frozenset[QubitId]] = {}

    def _validate_quantum_node(self, node: NodeReference) -> QuantumNode:
        """Get the QuantumNode for a node reference if the node is valid, else raise.

        Args:
            node (NodeReference): Reference to the node to validate.

        Returns:
            QuantumNode: Valid quantum node instance from the network.

        """
        node = self.network.validate_node(node)
        if not isinstance(node, QuantumNode):
            msg = "Node is not a quantum node."
            raise TypeError(msg)
        return node

    def _validate_qubit(self, qubit: QubitReference, *, needs_registered: bool = True) -> QubitId:
        """Get the QubitId for a qubit reference if the qubit is allocated, else raise.

        Args:
            qubit (QubitReference): Qubit reference to validate.
            needs_registered (bool): Whether the qubit needs to be registered. Defaults to True.

        Returns:
            QubitId: The qubit id.

        """
        if isinstance(qubit, Qubit) and qubit not in self.qubits.values():
            msg = f"Qubit {qubit} with id '{qubit.qid}' is not registered in the manager."
            raise ValueError(msg)

        qubit_id = (
            qubit.qid
            if isinstance(qubit, Qubit)
            else QubitId(qubit)
            if isinstance(qubit, str)
            else qubit
        )

        if needs_registered and qubit_id not in self.qubits:
            msg = f"Qubit with id '{qubit_id}' is not registered in the manager."
            raise ValueError(msg)

        return qubit_id

    def allocate_qubit(
        self,
        *,
        node: NodeReference,
        qubit_id: QubitId | str,
        qubit_type: QubitType = QubitType.COMMUNICATION,
    ) -> Qubit:
        """Allocate a new qubit in the system for a given node and type.

        Args:
            node (NodeReference): Reference to the node where the qubit resides.
            qubit_id (QubitId | str): Identifier for qubit.
            qubit_type (QubitType): Type of qubit to allocate. Defaults to Communication qubit.

        Returns:
            Qubit: The newly created and registered qubit.

        """
        node = self._validate_quantum_node(node)
        qubit_id = self._validate_qubit(qubit_id, needs_registered=False)
        qubit = Qubit(qubit_id, node, qubit_type)
        self._add_qubit(qubit)

        return qubit

    def _add_qubit(self, qubit: Qubit) -> None:
        """Add qubit to state system manager.

        Args:
            qubit (Qubit): The qubit we want to add.

        """
        if qubit.qid in self.qubits:
            msg = f"Qubit with ID {qubit.qid} already exists."
            raise ValueError(msg)
        self.qubits[qubit.qid] = qubit

    def move_qubit(self, qubit: QubitReference, new_node: NodeReference) -> None:
        """Allocate qubit to a new node.

        Args:
            qubit (QubitReference): Qubit reference of the qubit to be moved.
            new_node (NodeReference): Reference to the node to which qubit is to be moved.

        """
        qubit_id = self._validate_qubit(qubit)
        self.qubits[qubit_id].node = self._validate_quantum_node(new_node)

    def remove_qubit(self, qubit: QubitReference) -> None:
        """Remove qubit and corresponding state.

        Args:
            qubit (QubitReference): Reference of the qubit to be removed.

        """
        qubit_id = self._validate_qubit(qubit)

        if qubit_id in self.qubit_to_state_key:
            state_key = self.qubit_to_state_key[qubit_id]
            if state_key in self.entanglements:
                self.remove_entanglement(list(state_key))
            else:
                self.states.pop(state_key, None)
                self.qubit_to_state_key.pop(qubit_id, None)

        self.qubits.pop(qubit_id)

    def add_single_qubit_state(self, qubit: QubitReference, state: QuantumState) -> None:
        """Add or update the state of a single qubit.

        If the qubit is part of a single-qubit state, update it.
        If the qubit is part of a multi-qubit state, raise an error.

        Args:
            qubit (QubitReference): The qubit to assign the state to.
            state (QuantumState): The QuantumState for the qubit.

        """
        qubit_id = self._validate_qubit(qubit)

        if state.rho.shape != (2, 2):
            msg = "Single qubit state must be a 2x2 matrix."
            raise ValueError(msg)

        QuantumState.validate_density_matrix(state.rho)

        existing_key = self.qubit_to_state_key.get(qubit_id)
        if existing_key is not None:
            if len(existing_key) > 1:
                msg = (
                    f"Qubit {qubit_id} is currently part of an entangled state and "
                    "cannot be updated individually."
                )
                raise ValueError(msg)

            self.states.pop(existing_key, None)

        key = frozenset({qubit_id})
        self.states[key] = state
        self.qubit_to_state_key[qubit_id] = key

    def get_qubits_by_node(self, node: NodeReference) -> list[QubitId]:
        """Get all qubits located at a specific node.

        Args:
            node (NodeReference): Reference to the node.

        Returns:
            list[QubitId]: QubitIds allocated at certain node.

        """
        node = self._validate_quantum_node(node)
        return [qubit.qid for qubit in self.qubits.values() if qubit.node == node]

    def add_entanglement(self, entanglement: EntanglementLink, state: QuantumState) -> None:
        """Add entanglement to state system manager.

        If the qubits are part of single-qubit states, remove them.
        If the qubits are part of multi-qubit states, raise an error.

        Args:
            entanglement (EntanglementLink): The entanglement we want to add to the system.
            state (QuantumState): The according QuantumState we want to add to the system.

        """
        QuantumState.validate_density_matrix(state.rho)

        key = frozenset(entanglement.qubits)
        if key in self.entanglements:
            msg = "Entanglement already exists."
            raise ValueError(msg)
        for qid in key:
            self._validate_qubit(qid, needs_registered=True)

            existing_key = self.qubit_to_state_key.get(qid)
            if existing_key is not None and len(existing_key) > 1:
                msg = (
                    f"Qubit {qid} is already part of an entangled state "
                    f"({existing_key}) and cannot be added to a new entanglement."
                )
                raise ValueError(msg)

        for qid in key:
            existing_key = self.qubit_to_state_key.get(qid)
            if existing_key is not None:
                self.states.pop(existing_key, None)
                self.qubit_to_state_key.pop(qid, None)

        self.entanglements[key] = entanglement
        self.states[key] = state
        for qid in key:
            self.qubit_to_state_key[qid] = key

    def remove_entanglement(self, qubits: list[QubitReference]) -> None:
        """Remove entanglement from system.

        Args:
            qubits (list[QubitReference]): The list of qubits we want to remove.

        """
        qubit_ids = [self._validate_qubit(qid) for qid in qubits]

        key = frozenset(qubit_ids)
        self.entanglements.pop(key, None)
        self.states.pop(key, None)
        for qid in key:
            self.qubit_to_state_key.pop(qid, None)

    def allocate_bell_pair(
        self,
        nodes: list[NodeReference],
        qubit_ids: list[QubitId | str],
        current_time: int = 0,
        fidelity: float = 1.0,
    ) -> None:
        """Allocates two new communication qubits and a Bell state.

        Args:
            nodes (list[NodeReference]): References of the nodes.
            qubit_ids (list[QubitId | str]): Identifier of qubits.
            current_time (int): Time of Bell pair generation. Defaults to 0.
            fidelity (float): Fidelity of the entangled state. Defaults to 1.0.

        """
        if len(nodes) != BELL_PAIR_QUBITS or len(qubit_ids) != BELL_PAIR_QUBITS:
            msg = "Generation of Bell pair requires exactly 2 nodes and 2 qubits"
            raise ValueError(msg)

        nodes = [self._validate_quantum_node(node) for node in nodes]

        qubits = [
            self.allocate_qubit(
                node=nodes[i],
                qubit_id=qubit_ids[i],
                qubit_type=QubitType.COMMUNICATION,
            )
            for i in range(BELL_PAIR_QUBITS)
        ]

        bell_state = _create_bell_state(current_time, fidelity)
        entanglement = EntanglementLink(
            qubits=[qubits[0].qid, qubits[1].qid], creation_time=current_time
        )

        self.add_entanglement(entanglement, bell_state)

    @staticmethod
    def get_partial_trace(state: QuantumState, keep: list[int], dims: list[int]) -> QuantumState:
        """Retrieve state of a subsystem.

        Args:
            state (QuantumState): Quantum state we want to retrieve the substate from.
            keep (list[int]): List of indices of qubits to keep.
            dims (list[int]): Dimension for subsystem.

        Returns:
            QuantumState: The quantum state for specific qubit or qubits.

        """
        n = len(dims)
        traced_out = [i for i in range(n) if i not in keep]
        reshaped_rho = state.rho.reshape([2] * n * 2)
        for i in sorted(traced_out, reverse=True):
            reshaped_rho = np.trace(reshaped_rho, axis1=i, axis2=i + n)
        d = 2 ** len(keep)
        return QuantumState(rho=reshaped_rho.reshape((d, d)))

    def get_state(
        self, qubits: list[QubitReference], *, return_partial_state: bool | None
    ) -> QuantumState | None:
        """Retrieve (specific) state from system.

        If return_partial_state = True we return only the state of the input subsystem.

        Args:
            qubits (list[QubitReference]): Qubits we want to receive the state from.
            return_partial_state (bool | None): Whether a substate is returned or not.

        Returns:
            QuantumState or None: The quantum state for the specified qubits, or None if not found.

        """
        qubit_ids = [self._validate_qubit(qid) for qid in qubits]

        if len(qubit_ids) == 0:
            msg = "Empty qubits_ids list provided in the get_state method."
            raise ValueError(msg)

        key = frozenset(qubit_ids)
        state = self.states.get(key)

        if state is not None:
            return state

        possible_key = self.qubit_to_state_key.get(qubit_ids[0])
        if possible_key and key.issubset(possible_key):
            if not return_partial_state or return_partial_state is None:
                return self.states[possible_key]
            all_ids = sorted(possible_key, key=lambda qid: qid.value)
            sorted_qubit_ids = sorted(qubit_ids, key=lambda qid: qid.value)
            keep_indices = [all_ids.index(qid) for qid in sorted_qubit_ids]
            dims = [2] * len(all_ids)
            return self.get_partial_trace(self.states[possible_key], keep_indices, dims)

        return None
