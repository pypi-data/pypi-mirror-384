from collections.abc import Iterator

from kosmos.ml.config.sl_train import FLTrainConfig
from kosmos.ml.dataloader import make_train_test_dataloaders
from kosmos.ml.fl.fl_client import FLClient
from kosmos.ml.fl.fl_server import FLServer
from kosmos.ml.sl_result import SLTestIterationResult, SLTrainIterationResult
from kosmos.ml.sl_trainer import SLTrainer
from kosmos.topology.node import Node


class FLManager:
    """Federated learning manager for supervised learning classification tasks."""

    def __init__(
        self,
        config: FLTrainConfig,
        client_nodes: list[Node],
        server_node: Node,
    ) -> None:
        """Initialize the federated learning manager.

        Args:
            config (FLTrainConfig): Federated learning training configuration.
            client_nodes (list[Node]): The nodes representing federated clients.
            server_node (Node): The node representing the federated server.

        """
        self.config = config
        self.client_nodes = client_nodes
        self.server_node = server_node

        self.dataset = config.dataset
        self.num_rounds = config.num_rounds
        self.num_epochs = config.num_epochs

        self.train_loaders, self.test_loader = make_train_test_dataloaders(
            self.dataset,
            self.config.train_split,
            self.config.batch_size,
            num_train_subsets=len(self.client_nodes),
        )

        self.clients: list[FLClient] | None = None
        self.server: FLServer | None = None
        self._init_clients()
        self._init_server()

    def _get_trainer_instance(self) -> SLTrainer:
        """Create a new trainer based on the configuration.

        Returns:
            SLTrainer: The trainer instance.

        """
        model = self.config.model_config.get_instance(
            self.dataset.input_dimension, self.dataset.output_dim
        )
        return SLTrainer(
            model,
            self.config.optimizer_config,
            self.config.lr_scheduler_config,
            self.config.loss_config,
            self.config.max_grad_norm,
        )

    def _init_clients(self) -> None:
        """Initialize the clients."""
        clients: list[FLClient] = []
        for client_node in self.client_nodes:
            trainer = self._get_trainer_instance()
            client = FLClient(trainer, client_node)
            clients.append(client)
        self.clients = clients

    def _init_server(self) -> None:
        """Initialize the server."""
        trainer = self._get_trainer_instance()
        self.server = FLServer(trainer, self.server_node)

    def train(self) -> Iterator[SLTrainIterationResult]:
        """Run federated training across all configured rounds.

        Returns:
            Iterator[SLTrainIterationResult]: An iterator yielding one training result per epoch
                                              for all rounds.

        """
        for fl_round in range(self.num_rounds):
            yield from self._run_round(fl_round)

    def test(self) -> SLTestIterationResult:
        """Evaluate the global model on the test dataset.

        Returns:
            SLTrainIterationResult: The result of the global model evaluation.

        """
        return self.server.test(self.test_loader)

    def _run_round(self, fl_round: int) -> Iterator[SLTrainIterationResult]:
        """Run a single round of federated learning.

        Args:
            fl_round (int): The index of the federated learning round.

        Returns:
            Iterator[SLTrainIterationResult]: An iterator yielding one training result per epoch.

        """
        server_state = self.server.get_model_state()
        client_states = []

        for i, client in enumerate(self.clients):
            client.set_model_state(server_state)
            yield from client.train(self.num_epochs, self.train_loaders[i], fl_round)
            client_states.append(client.get_model_state())

        self.server.aggregate(client_states)
