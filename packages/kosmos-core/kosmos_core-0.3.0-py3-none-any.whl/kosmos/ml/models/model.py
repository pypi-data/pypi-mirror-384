from abc import ABC, abstractmethod

import torch
from torch import nn


class Model(nn.Module, ABC):
    """Base class for models."""

    def __init__(self, input_dim: int, output_dim: int) -> None:
        """Initialize the model.

        Args:
            input_dim (int): Model input dimension.
            output_dim (int): Model output dimension.

        """
        super().__init__()
        self.input_dim = input_dim
        self.output_dim = output_dim

    @abstractmethod
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Perform a forward pass.

        Args:
            x (torch.Tensor): Input tensor.

        Returns:
            torch.Tensor: Output tensor.

        """
