from abc import ABC, abstractmethod

from torch.optim import Optimizer
from torch.optim.lr_scheduler import CosineAnnealingLR, ExponentialLR, LRScheduler, StepLR


class LearningRateSchedulerConfig(ABC):
    """Learning rate scheduler configuration."""

    @abstractmethod
    def get_instance(self, optimizer: Optimizer) -> LRScheduler:
        """Get the learning rate scheduler instance.

        Returns:
            LRScheduler: Learning rate scheduler instance.

        """


class StepLearningRateSchedulerConfig(LearningRateSchedulerConfig):
    """Step learning rate scheduler configuration."""

    def __init__(self, step_size: int, gamma: float = 0.1) -> None:
        """Initialize the step learning rate scheduler configuration.

        Args:
            step_size (int): Period of learning rate decay.
            gamma (float): Multiplicative factor of learning rate decay. Defaults to 0.1.

        """
        self.step_size = step_size
        self.gamma = gamma

    def get_instance(self, optimizer: Optimizer) -> StepLR:
        """Get the step learning rate scheduler instance.

        Args:
            optimizer (Optimizer): Optimizer instance.

        Returns:
            StepLR: Step learning rate scheduler instance.

        """
        return StepLR(optimizer, step_size=self.step_size, gamma=self.gamma)


class ExponentialLearningRateSchedulerConfig(LearningRateSchedulerConfig):
    """Exponential learning rate scheduler configuration."""

    def __init__(self, gamma: float) -> None:
        """Initialize the exponential learning rate scheduler configuration.

        Args:
            gamma (float): Multiplicative factor of learning rate decay.

        """
        self.gamma = gamma

    def get_instance(self, optimizer: Optimizer) -> ExponentialLR:
        """Get the exponential learning rate scheduler instance.

        Args:
            optimizer (Optimizer): Optimizer instance.

        Returns:
            ExponentialLR: Exponential learning rate scheduler instance.

        """
        return ExponentialLR(optimizer, gamma=self.gamma)


class CosineLearningRateSchedulerConfig(LearningRateSchedulerConfig):
    """Cosine annealing learning rate scheduler configuration."""

    def __init__(self, max_epochs: int, min_lr: float = 0.0) -> None:
        """Initialize the cosine learning rate scheduler configuration.

        Args:
            max_epochs (int): Maximum number of epochs (iterations for the scheduler).
            min_lr (float): Minimum learning rate. Defaults to 0.0.

        """
        self.max_epochs = max_epochs
        self.min_lr = min_lr

    def get_instance(self, optimizer: Optimizer) -> CosineAnnealingLR:
        """Get the cosine learning rate scheduler instance.

        Args:
            optimizer (Optimizer): Optimizer instance.

        Returns:
            CosineAnnealingLR: Cosine learning rate scheduler instance.

        """
        return CosineAnnealingLR(optimizer, T_max=self.max_epochs, eta_min=self.min_lr)
