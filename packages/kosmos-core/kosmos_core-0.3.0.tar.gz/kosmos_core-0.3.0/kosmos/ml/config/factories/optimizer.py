from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import Any

import torch
from torch.optim import SGD, Adam, Optimizer

type ParamsT = (
    Iterable[torch.Tensor] | Iterable[dict[str, Any]] | Iterable[tuple[str, torch.Tensor]]
)


class OptimizerConfig(ABC):
    """Optimizer configuration."""

    @abstractmethod
    def get_instance(self, params: ParamsT) -> Optimizer:
        """Get the optimizer instance.

        Args:
            params (ParamsT): Parameters to optimize.

        Returns:
            Optimizer: Optimizer instance.

        """


class SGDOptimizerConfig(OptimizerConfig):
    """Stochastic gradient descent (SGD) optimizer configuration."""

    def __init__(
        self,
        lr: float = 1e-3,
        momentum: float = 0.0,
        weight_decay: float = 0.0,
        *,
        nesterov: bool = False,
    ) -> None:
        """Initialize the SGD optimizer configuration.

        Args:
            lr (float): Learning rate. Defaults to 1e-3.
            momentum (float): Momentum factor. Defaults to 0.0.
            weight_decay (float): Weight decay. Defaults to 0.0.
            nesterov (bool): Whether to use Nesterov momentum. Only applicable
                             when momentum is non-zero. Defaults to False.

        """
        self.lr = lr
        self.momentum = momentum
        self.weight_decay = weight_decay
        self.nesterov = nesterov

    def get_instance(self, params: ParamsT) -> SGD:
        """Get the SGD optimizer instance.

        Args:
            params (ParamsT): Parameters to optimize.

        Returns:
            SGD: SGD optimizer instance.

        """
        return SGD(
            params,
            lr=self.lr,
            momentum=self.momentum,
            weight_decay=self.weight_decay,
            nesterov=self.nesterov,
        )


class AdamOptimizerConfig(OptimizerConfig):
    """Adam optimizer configuration."""

    def __init__(self, lr: float = 1e-3, weight_decay: float = 0.0) -> None:
        """Initialize the Adam optimizer configuration.

        Args:
            lr (float): Learning rate. Defaults to 1e-3.
            weight_decay (float): Weight decay. Defaults to 0.0.

        """
        self.lr = lr
        self.weight_decay = weight_decay

    def get_instance(self, params: ParamsT) -> Adam:
        """Get the Adam optimizer instance.

        Args:
            params (ParamsT): Parameters to optimize.

        Returns:
            Adam: Adam optimizer instance.

        """
        return Adam(params, lr=self.lr, weight_decay=self.weight_decay)
