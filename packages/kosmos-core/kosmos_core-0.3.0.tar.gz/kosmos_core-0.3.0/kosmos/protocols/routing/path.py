from dataclasses import dataclass

from kosmos.topology.link import Link
from kosmos.topology.node import Node


@dataclass
class Path:
    """Path between two nodes.

    Attributes:
        nodes (list[Node]): List of nodes in the path.
        links (list[Link]): List of links in the path.

    """

    nodes: list[Node]
    links: list[Link]

    def __post_init__(self) -> None:
        """Validate the path."""
        if not self.nodes:
            msg = "A path must have at least one node."
            raise ValueError(msg)
        if len(self.nodes) != len(self.links) + 1:
            msg = "The number of nodes must be one more than the number of links."
            raise ValueError(msg)

    def __str__(self) -> str:
        """Return a human-readable string including node and link IDs."""
        parts: list[str] = []
        for i, node in enumerate(self.nodes[:-1]):
            link = self.links[i] if i < len(self.links) else None
            if link:
                parts.append(f"{node.id} -[{link.id}]->")
        parts.append(str(self.nodes[-1].id))

        return " ".join(parts)
