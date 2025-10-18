from abc import ABC
from dataclasses import dataclass

from kosmos.ml.sl_metrics import SLMetrics
from kosmos.topology.node import Node


def _format_node_id_value(value: str, length: int) -> str:
    """Format a node ID value to a fixed length.

    Args:
        value (str): The node ID value.
        length (int): The fixed length.

    """
    if len(value) > length:
        return value[: length - 3] + "..."
    return value.ljust(length)


@dataclass
class SLIterationResult(ABC):
    """Result of a supervised learning iteration.

    Attributes:
        loss (float): Mean loss value over the iteration.
        metrics (SLMetrics): Evaluation metrics for the iteration.

    """

    loss: float
    metrics: SLMetrics

    def __str__(self) -> str:
        """Return a human-readable string with the loss and metrics formatted to four decimals."""
        return f"Loss: {self.loss:.4f} | {self.metrics}"


@dataclass
class SLTrainIterationResult(SLIterationResult):
    """Result of a supervised learning training iteration.

    Attributes:
        loss (float): Mean loss value over the iteration.
        metrics (SLMetrics): Evaluation metrics for the iteration.
        epoch (int): Epoch index corresponding to this iteration.
        fl_round (int | None): Federated learning round index corresponding to this iteration.
                               Defaults to None.
        node (Node | None): The node corresponding to this iteration. Defaults to None.

    """

    epoch: int
    fl_round: int | None = None
    node: Node | None = None

    def __str__(self) -> str:
        """Return a human-readable string with the loss and metrics formatted to four decimals."""
        desc = ""
        if self.node is not None:
            formatted_id = _format_node_id_value(self.node.id.value, 10)
            desc += f"{formatted_id} | "
        if self.fl_round is not None:
            desc += f"Round {self.fl_round:4d}".ljust(10) + " | "
        desc += f"Epoch {self.epoch:4d}".ljust(10) + " | " + super().__str__()
        return desc


@dataclass
class SLTestIterationResult(SLIterationResult):
    """Result of a supervised learning test iteration.

    Attributes:
        loss (float): Mean loss value over the iteration.
        metrics (SLMetrics): Evaluation metrics for the iteration.

    """

    def __str__(self) -> str:
        """Return a human-readable string with the loss and metrics formatted to four decimals."""
        return "Test".ljust(10) + " | " + super().__str__()
