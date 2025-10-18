from dataclasses import dataclass
from enum import Enum

from kosmos.topology.node import QuantumNode


@dataclass(frozen=True)
class QubitId:
    """Identifier of a qubit.

    Attributes:
        value (str): Identifier string.

    """

    value: str

    def __post_init__(self) -> None:
        """Validate that the value is non-empty."""
        if not self.value or not self.value.strip():
            msg = "QubitId must be a non-empty string."
            raise ValueError(msg)

    def __str__(self) -> str:
        """Return the string value."""
        return self.value


class QubitType(Enum):
    """Type of qubit based on its intended use."""

    DATA = "data"
    COMMUNICATION = "communication"


class Qubit:
    """Representation of a physical qubit in the network."""

    def __init__(self, qid: QubitId, node: QuantumNode, qubit_type: QubitType) -> None:
        """Initialize with input validation.

        Args:
            qid (QubitId): Unique qubit identifier.
            node (QuantumNode): The quantum node where this qubit is located.
            qubit_type (QubitType): Type of the qubit.

        """
        self._qid = qid
        self._node = node
        self._qubit_type = qubit_type

    @property
    def qid(self) -> "QubitId":
        """Qubit ID (read-only)."""
        return self._qid

    @property
    def node(self) -> QuantumNode:
        """Qubit's node."""
        return self._node

    @node.setter
    def node(self, node: QuantumNode) -> None:
        self._node = node

    @property
    def qubit_type(self) -> "QubitType":
        """Qubit's type."""
        return self._qubit_type

    @qubit_type.setter
    def qubit_type(self, qubit_type: QubitType) -> None:
        self._qubit_type = qubit_type
