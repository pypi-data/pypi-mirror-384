from collections.abc import Iterator

from torch.utils.data import DataLoader

from kosmos.ml.sl_result import SLTrainIterationResult
from kosmos.ml.sl_trainer import SLTrainer
from kosmos.topology.node import Node


class FLClient:
    """Federated learning client."""

    def __init__(self, trainer: SLTrainer, node: Node) -> None:
        """Initialize a federated learning client.

        Args:
            trainer (SLTrainer): The trainer used for local training.
            node (Node): The node representing this client in the topology.

        """
        self.trainer = trainer
        self.node = node

        self.model = self.trainer.model

    def get_model_state(self) -> dict:
        """Get the current model state of the client.

        Returns:
            dict: A state_dict containing the model parameters.

        """
        return self.model.state_dict()

    def set_model_state(self, state_dict: dict) -> None:
        """Set the client's model state.

        Args:
            state_dict (dict): The state_dict to set the client's model state to.

        """
        self.model.load_state_dict(state_dict)

    def train(
        self, num_epochs: int, dataloader: DataLoader, fl_round: int
    ) -> Iterator[SLTrainIterationResult]:
        """Train the client's model on the given data.

        Args:
            num_epochs (int): Number of epochs to run.
            dataloader (DataLoader): Dataloader providing the local training data.
            fl_round (int): The federated learning round index for this training run.

        Returns:
            Iterator[SLTrainIterationResult]: An iterator yielding one training result per epoch.

        """
        yield from self.trainer.train(num_epochs, dataloader, fl_round, self.node)
