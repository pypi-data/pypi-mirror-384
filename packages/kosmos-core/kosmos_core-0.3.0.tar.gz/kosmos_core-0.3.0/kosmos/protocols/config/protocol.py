import math
from collections.abc import Collection
from dataclasses import dataclass
from typing import Literal

from kosmos.topology.link import LinkType


@dataclass(frozen=True, kw_only=True)
class ProtocolConfig:
    """Base class for all protocol configurations."""


@dataclass(frozen=True, kw_only=True)
class EGProtocolConfig(ProtocolConfig):
    """Entanglement generation protocol configuration.

    Attributes:
        fidelity_threshold (float): Threshold for entanglement fidelity.
        max_retries (int): Maximum number of retries.

    """

    fidelity_threshold: float
    max_retries: int

    def __post_init__(self) -> None:
        """Validate the protocol configuration."""
        if not 0 <= self.fidelity_threshold <= 1:
            msg = "fidelity_threshold must be in [0, 1]."
            raise ValueError(msg)
        if self.max_retries < 1 or not math.isfinite(self.max_retries):
            msg = "max_retries must be >= 1 and finite."
            raise ValueError(msg)


@dataclass(frozen=True, kw_only=True)
class RoutingProtocolConfig(ProtocolConfig):
    """Routing protocol configuration.

    Attributes:
        allowed_link_types (Collection[LinkType]): Allowed link types for routing.
        cost_function (Literal["cost", "distance"]): Cost function to use for routing.
            Defaults to 'cost'.

    """

    allowed_link_types: Collection[LinkType]
    cost_function: Literal["cost", "distance"] = "cost"

    def __post_init__(self) -> None:
        """Make allowed_link_types immutable."""
        allowed_link_types_fs = frozenset(self.allowed_link_types)
        object.__setattr__(self, "allowed_link_types", allowed_link_types_fs)
