from dataclasses import dataclass

from kosmos.ml.config.factories.loss import LossConfig
from kosmos.ml.config.factories.lr_scheduler import LearningRateSchedulerConfig
from kosmos.ml.config.factories.model import ModelConfig
from kosmos.ml.config.factories.optimizer import OptimizerConfig
from kosmos.ml.datasets.dataset import SLDataset


@dataclass(frozen=True, kw_only=True)
class SLTrainConfig:
    """Supervised learning training configuration.

    Attributes:
        dataset (SLDataset): Supervised learning dataset.
        train_split (float): Fraction of dataset for training. Test split is 1 - train_split.
        batch_size (int): Number of samples per batch.
        num_epochs (int): Number of training epochs.
        model_config (ModelConfig): Model configuration.
        optimizer_config (OptimizerConfig): Optimizer configuration.
        lr_scheduler_config (LearningRateSchedulerConfig | None): Learning rate scheduler
                                                                  configuration. Defaults to None.
        max_grad_norm (float | None): Maximum gradient norm. Defaults to 1.0.
        loss_config (LossConfig): Loss function configuration.

    """

    dataset: SLDataset
    train_split: float
    batch_size: int
    num_epochs: int
    model_config: ModelConfig
    optimizer_config: OptimizerConfig
    lr_scheduler_config: LearningRateSchedulerConfig | None = None
    max_grad_norm: float | None = 1.0
    loss_config: LossConfig

    def __post_init__(self) -> None:
        """Validate the train configuration."""
        if not (0.0 < self.train_split < 1.0):
            msg = "train_split must be in (0,1)."
            raise ValueError(msg)
        if self.batch_size <= 0:
            msg = "batch_size must be > 0."
            raise ValueError(msg)
        if self.num_epochs <= 0:
            msg = "num_epochs must be > 0."
            raise ValueError(msg)


@dataclass(frozen=True, kw_only=True)
class FLTrainConfig(SLTrainConfig):
    """Federated learning training configuration.

    Attributes:
        dataset (SLDataset): Supervised learning dataset.
        train_split (float): Fraction of dataset for training. Test split is 1 - train_split.
        batch_size (int): Number of samples per batch.
        num_epochs (int): Number of training epochs.
        model_config (ModelConfig): Model configuration.
        optimizer_config (OptimizerConfig): Optimizer configuration.
        lr_scheduler_config (LearningRateSchedulerConfig | None): Learning rate scheduler
                                                                  configuration. Defaults to None.
        max_grad_norm (float | None): Maximum gradient norm. Defaults to 1.0.
        loss_config (LossConfig): Loss function configuration.
        num_rounds (int): Number of federated learning rounds.

    """

    num_rounds: int

    def __post_init__(self) -> None:
        """Validate the train configuration."""
        super().__post_init__()
        if self.num_rounds <= 0:
            msg = "num_rounds must be > 0."
            raise ValueError(msg)
