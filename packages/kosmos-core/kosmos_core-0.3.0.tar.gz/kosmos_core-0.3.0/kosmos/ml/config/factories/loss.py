from abc import ABC, abstractmethod

from torch.nn import CrossEntropyLoss, Module


class LossConfig(ABC):
    """Loss function configuration for training."""

    @abstractmethod
    def get_instance(self) -> Module:
        """Get the loss module instance.

        Returns:
            Module: Loss module instance.

        """


class CrossEntropyLossConfig(LossConfig):
    """Cross-entropy loss function configuration."""

    def get_instance(self) -> CrossEntropyLoss:
        """Get the cross-entropy loss instance.

        Returns:
            CrossEntropyLoss: Cross-entropy loss instance.

        """
        return CrossEntropyLoss()
