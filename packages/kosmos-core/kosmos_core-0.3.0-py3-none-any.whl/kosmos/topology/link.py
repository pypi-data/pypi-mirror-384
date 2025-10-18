import math
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import ClassVar

from kosmos.topology.node import Node


@dataclass(frozen=True)
class LinkId:
    """Identifier of a link.

    Attributes:
        value (str): Identifier string.

    """

    value: str

    def __post_init__(self) -> None:
        """Validate that the value is non-empty."""
        if not self.value or not self.value.strip():
            msg = "LinkId must be a non-empty string."
            raise ValueError(msg)

    def __str__(self) -> str:
        """Return the string value."""
        return self.value


class LinkType(Enum):
    """Type of link."""

    QUANTUM = "quantum"
    CLASSICAL = "classical"


@dataclass(frozen=True, kw_only=True)
class Link(ABC):
    """Base for undirected links between two nodes.

    Attributes:
        id (LinkId): Link identifier.
        label (str | None): Label of the link. Defaults to None.
        src (Node): Source node.
        dst (Node): Destination node.

    """

    id: LinkId
    label: str | None = None
    src: Node
    dst: Node

    def __post_init__(self) -> None:
        """Validate the link."""
        if self.label is not None and not self.label.strip():
            msg = "label must be None or a non-empty string."
            raise ValueError(msg)
        if self.src == self.dst:
            msg = "src and dst must be different nodes."
            raise ValueError(msg)

    @property
    @abstractmethod
    def type(self) -> LinkType:
        """Type of the link."""

    @property
    @abstractmethod
    def weight(self) -> float:
        """Cost of the link."""


@dataclass(frozen=True, kw_only=True)
class OpticalLink(Link):
    """Base for optical fiber links.

    Attributes:
        id (LinkId): Link identifier.
        label (str | None): Label of the link. Defaults to None.
        src (Node): Source node.
        dst (Node): Destination node.
        distance (float): Length of the fiber in meters.
        attenuation (float): Attenuation of the fiber in dB/m.
        signal_speed (float): Propagation speed in m/ps.

    """

    distance: float
    attenuation: float
    signal_speed: float

    def __post_init__(self) -> None:
        """Validate the optical link."""
        super().__post_init__()
        if self.distance < 0 or not math.isfinite(self.distance):
            msg = "distance must be >= 0 and finite."
            raise ValueError(msg)
        if self.attenuation < 0 or not math.isfinite(self.attenuation):
            msg = "attenuation must be >= 0 and finite."
            raise ValueError(msg)
        if self.signal_speed <= 0 or not math.isfinite(self.signal_speed):
            msg = "signal_speed must be > 0 and finite."
            raise ValueError(msg)

    @property
    def delay(self) -> float:
        """Propagation delay in ps."""
        return self.distance / self.signal_speed

    @property
    def total_attenuation(self) -> float:
        """Total attenuation in dB."""
        return self.distance * self.attenuation

    @property
    def transmissivity(self) -> float:
        """Transmitted fraction."""
        return math.pow(10.0, -self.total_attenuation / 10.0)

    @property
    def loss(self) -> float:
        """Loss rate for transmitted photons."""
        loss_raw = 1.0 - self.transmissivity
        return max(0.0, min(loss_raw, 1.0))

    @property
    @abstractmethod
    def type(self) -> LinkType:
        """Type of the link."""

    @property
    @abstractmethod
    def weight(self) -> float:
        """Cost of the link."""


@dataclass(frozen=True, kw_only=True)
class ClassicalLink(OpticalLink):
    """Classical optical fiber link.

    Attributes:
        id (LinkId): Link identifier.
        label (str | None): Label of the link. Defaults to None.
        src (Node): Source node.
        dst (Node): Destination node.
        distance (float): Length of the fiber in meters.
        attenuation (float): Attenuation of the fiber in dB/m.
        signal_speed (float): Propagation speed in m/ps.
        bandwidth (float): Link bandwidth in bit/s.

    """

    bandwidth: float

    _TYPE: ClassVar[LinkType] = LinkType.CLASSICAL

    def __post_init__(self) -> None:
        """Validate the classical link."""
        super().__post_init__()
        if self.bandwidth <= 0 or not math.isfinite(self.bandwidth):
            msg = "bandwidth must be > 0 and finite."
            raise ValueError(msg)

    @property
    def type(self) -> LinkType:
        """Type of the link."""
        return self._TYPE

    @property
    def weight(self) -> float:
        """Heuristic cost of the classical link."""
        return self.delay * (1 + self.loss) / self.bandwidth


@dataclass(frozen=True, kw_only=True)
class QuantumLink(OpticalLink):
    """Quantum optical fiber link.

    Attributes:
        id (LinkId): Link identifier.
        label (str | None): Label of the link. Defaults to None.
        src (Node): Source node.
        dst (Node): Destination node.
        distance (float): Length of the fiber in meters.
        attenuation (float): Attenuation of the fiber in dB/m.
        signal_speed (float): Propagation speed in m/ps.
        polarization_fidelity (float): Probability of no polarization error. Defaults to 1.0.
        repetition_rate (float): Photon generation repetition rate in Hz.

    """

    polarization_fidelity: float = 1.0
    repetition_rate: float

    _TYPE: ClassVar[LinkType] = LinkType.QUANTUM

    def __post_init__(self) -> None:
        """Validate the quantum link."""
        super().__post_init__()
        if not (0 <= self.polarization_fidelity <= 1):
            msg = "polarization_fidelity must be in [0, 1]."
            raise ValueError(msg)
        if self.repetition_rate <= 0 or not math.isfinite(self.repetition_rate):
            msg = "repetition_rate must be > 0 and finite."
            raise ValueError(msg)

    @property
    def type(self) -> LinkType:
        """Type of the link."""
        return self._TYPE

    @property
    def weight(self) -> float:
        """Heuristic cost of the quantum link."""
        return self.delay * (1 + self.loss) / self.repetition_rate
