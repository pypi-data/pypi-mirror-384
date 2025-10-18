from collections.abc import Iterator

from kosmos.ml.config.sl_train import SLTrainConfig
from kosmos.ml.dataloader import make_train_test_dataloaders
from kosmos.ml.sl_result import SLTestIterationResult, SLTrainIterationResult
from kosmos.ml.sl_trainer import SLTrainer


class CLManager:
    """Centralized learning manager for supervised learning classification tasks."""

    def __init__(
        self,
        config: SLTrainConfig,
    ) -> None:
        """Initialize the centralized learning manager.

        Args:
            config: Supervised learning training configuration.

        """
        self.config = config

        self.dataset = self.config.dataset

        self.model = self.config.model_config.get_instance(
            self.dataset.input_dimension, self.dataset.output_dim
        )

        self.trainer = SLTrainer(
            self.model,
            self.config.optimizer_config,
            self.config.lr_scheduler_config,
            self.config.loss_config,
            self.config.max_grad_norm,
        )

        train_loaders, self.test_loader = make_train_test_dataloaders(
            self.dataset,
            self.config.train_split,
            self.config.batch_size,
        )
        self.train_loader = train_loaders[0]

    def train(self) -> Iterator[SLTrainIterationResult]:
        """Run training on the train data over the configured number of epochs.

        Returns:
            Iterator[SLTrainIterationResult]: An iterator yielding one train result per epoch.

        """
        yield from self.trainer.train(self.config.num_epochs, self.train_loader)

    def test(self) -> SLTestIterationResult:
        """Evaluate the model on the test data.

        Returns:
            SLTestIterationResult: Result of the test iteration.

        """
        return self.trainer.test(self.test_loader)
