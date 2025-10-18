from kosmos.quantum_logic.qubit import QubitId

MINIMUM_ENTANGLEMENT_QUBITS = 2


class EntanglementLink:
    """Metadata about an entangled connection between qubits."""

    def __init__(self, qubits: list[QubitId], creation_time: int) -> None:
        """Initialize with input validation.

        Args:
            qubits (list[QubitId]): List of qubits participating in the entangled state.
            creation_time (int): Timestamp when the entanglement was created.

        """
        if not qubits or len(qubits) < MINIMUM_ENTANGLEMENT_QUBITS:
            msg = "An EntanglementLink must involve at least 2 qubits."
            raise ValueError(msg)

        self._qubits = qubits
        self._creation_time = creation_time

    @property
    def creation_time(self) -> int:
        """Creation time of an Entanglement Link."""
        return self._creation_time

    @property
    def qubits(self) -> list[QubitId]:
        """Qubits related with this entanglement link."""
        return self._qubits

    def remove_qubit(self, qubit: QubitId) -> None:
        """Remove qubit from entanglement.

        Args:
            qubit (Qubit): Qubit to be removed.

        """
        if qubit not in self._qubits:
            msg = f"Qubit {qubit} not found in this entanglement."
            raise ValueError(msg)

        if len(self._qubits) <= MINIMUM_ENTANGLEMENT_QUBITS:
            msg = "Cannot remove qubit, would leave fewer than 2 qubits."
            raise ValueError(msg)

        self._qubits.remove(qubit)

    def append_qubit(self, new_qubit: QubitId) -> None:
        """Append qubit to entanglement.

        Args:
            new_qubit (QubitId): Qubit to be added.

        """
        self._qubits.append(new_qubit)
