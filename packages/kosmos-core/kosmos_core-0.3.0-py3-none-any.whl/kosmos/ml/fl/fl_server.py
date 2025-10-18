import torch
from torch.utils.data import DataLoader

from kosmos.ml.sl_result import SLTestIterationResult
from kosmos.ml.sl_trainer import SLTrainer
from kosmos.topology.node import Node


class FLServer:
    """Federated learning server."""

    def __init__(self, trainer: SLTrainer, node: Node) -> None:
        """Initialize a federated learning server.

        Args:
            trainer (SLTrainer): The trainer used by this server.
            node (Node): The node representing this server in the topology.

        """
        self.trainer = trainer
        self.node = node

        self.model = self.trainer.model

    def get_model_state(self) -> dict:
        """Get the current model state of the server.

        Returns:
            dict: A state_dict containing the model parameters.

        """
        return self.model.state_dict()

    def aggregate(self, client_states: list[dict]) -> None:
        """Aggregate model states from clients using simple averaging.

        Args:
            client_states (list[dict]): A list of model state_dicts from clients.

        """
        global_dict = self.model.state_dict()
        for key in global_dict:
            global_dict[key] = torch.stack(
                [cs[key].detach().clone() for cs in client_states]
            ).mean(dim=0)
        self.model.load_state_dict(global_dict)

    def test(self, dataloader: DataLoader) -> SLTestIterationResult:
        """Evaluate the global model on test data.

        Args:
            dataloader (DataLoader): Dataloader providing the test data.

        Returns:
            SLTestIterationResult: The result of the test iteration.

        """
        return self.trainer.test(dataloader)
