import math
from abc import ABC, abstractmethod
from collections.abc import Collection
from dataclasses import dataclass
from enum import Enum
from typing import ClassVar


@dataclass(frozen=True)
class NodeId:
    """Identifier of a node.

    Attributes:
        value (str): Identifier string.

    """

    value: str

    def __post_init__(self) -> None:
        """Validate that the value is non-empty."""
        if not self.value or not self.value.strip():
            msg = "NodeId must be a non-empty string."
            raise ValueError(msg)

    def __str__(self) -> str:
        """Return the string value."""
        return self.value


class NodeType(Enum):
    """Type of node."""

    CLASSICAL = "classical"
    QUANTUM = "quantum"


class NodeRole(Enum):
    """Role of a node."""

    END_USER = "end_user"
    ROUTER = "router"
    REPEATER = "repeater"


@dataclass(frozen=True, kw_only=True)
class Node(ABC):
    """Base for network nodes.

    Attributes:
        id (NodeId): Node identifier.
        label (str | None): Label of the node. Defaults to None.
        roles (Collection[NodeRole]): Role(s) of the node.

    """

    id: NodeId
    label: str | None = None
    roles: Collection[NodeRole]

    def __post_init__(self) -> None:
        """Make roles immutable and validate the node."""
        if self.label is not None and not self.label.strip():
            msg = "label must be None or a non-empty string."
            raise ValueError(msg)

        roles_fs = frozenset(self.roles)
        object.__setattr__(self, "roles", roles_fs)
        if not all(isinstance(r, NodeRole) for r in roles_fs):
            msg = "roles must contain only NodeRole members."
            raise TypeError(msg)

    @property
    @abstractmethod
    def type(self) -> NodeType:
        """Type of the node."""

    def has_role(self, role: NodeRole) -> bool:
        """Check if this node has a given role.

        Args:
            role: Role to check.

        Returns:
            True if the role is present.

        """
        return role in self.roles


@dataclass(frozen=True, kw_only=True)
class ClassicalNode(Node):
    """Classical node.

    Attributes:
        id (NodeId): Node identifier.
        label (str | None): Label of the node. Defaults to None.
        roles (Collection[NodeRole]): Role(s) of the node.

    """

    _TYPE: ClassVar[NodeType] = NodeType.CLASSICAL

    @property
    def type(self) -> NodeType:
        """Type of the node."""
        return self._TYPE


@dataclass(frozen=True, kw_only=True)
class QuantumNode(Node):
    """Quantum node.

    Attributes:
        id (NodeId): Node identifier.
        label (str | None): Label of the node. Defaults to None.
        roles (Collection[NodeRole]): Role(s) of the node.
        num_qubits (int): Number of physical qubits.
        gate_fid (float): Fidelity of multi-qubit gates. Defaults to 1.0.
        meas_fid (float): Fidelity of single-qubit measurements. Defaults to 1.0.
        coherence_time (float): Maximum storage time before decoherence in seconds.
        has_transceiver (bool): Whether the node has a quantum transceiver. Defaults to False.

    """

    num_qubits: int
    gate_fid: float = 1.0
    meas_fid: float = 1.0
    coherence_time: float
    has_transceiver: bool = False

    _TYPE: ClassVar[NodeType] = NodeType.QUANTUM

    def __post_init__(self) -> None:
        """Validate the node."""
        super().__post_init__()
        if self.num_qubits < 0 or not math.isfinite(self.num_qubits):
            msg = "num_qubits must be >= 0 and finite."
            raise ValueError(msg)
        if not (0 <= self.gate_fid <= 1):
            msg = "gate_fid must be in [0, 1]."
            raise ValueError(msg)
        if not (0 <= self.meas_fid <= 1):
            msg = "meas_fid must be in [0, 1]."
            raise ValueError(msg)
        if self.coherence_time <= 0 or not math.isfinite(self.coherence_time):
            msg = "coherence_time must be > 0 and finite."
            raise ValueError(msg)

    @property
    def type(self) -> NodeType:
        """Type of the node."""
        return self._TYPE
