from abc import ABC
from dataclasses import dataclass

from kosmos.protocols.routing.path import Path
from kosmos.protocols.status import ProtocolStatus


@dataclass
class ProtocolResult(ABC):
    """Result of protocol execution.

    Attributes:
        status (ProtocolStatus): Status of the protocol.

    """

    status: ProtocolStatus


@dataclass
class EGProtocolResult(ProtocolResult):
    """Entanglement generation protocol result.

    Attributes:
        status (ProtocolStatus): Status of the protocol.

    """


@dataclass
class RoutingProtocolResult(ProtocolResult):
    """Routing protocol result.

    Attributes:
        status (ProtocolStatus): Status of the protocol.
        path (Path | None): Resulting path of the routing protocol. None if no path was found.
        total_cost (float | None): Total cost of the resulting path. None if no path was found.
        total_distance (float | None): Total distance of the resulting path. None if no path was
            found.

    """

    path: Path | None
    total_cost: float | None
    total_distance: float | None

    def __str__(self) -> str:
        """Return a human-readable string with the path and metrics formatted to four decimals."""
        desc = ""
        if self.path is not None:
            desc += "Path: " + str(self.path) + "\n"
        else:
            return "No path found."
        if self.total_cost is not None:
            desc += f"Total cost: {self.total_cost:.4g}\n"
        if self.total_distance is not None:
            desc += f"Total distance: {self.total_distance:.4f}\n"
        return desc.strip()
