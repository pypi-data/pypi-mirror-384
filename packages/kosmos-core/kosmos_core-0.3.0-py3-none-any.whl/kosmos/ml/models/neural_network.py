import torch
from torch import nn

from kosmos.ml.models.model import Model


class NeuralNetwork(Model):
    """Feedforward neural network."""

    def __init__(self, input_dim: int, output_dim: int, hidden_layers: list[int]) -> None:
        """Initialize the neural network.

        Args:
            input_dim (int): The input dimension of the model.
            output_dim (int): The output dimension of the model.
            hidden_layers (list[int]): Sizes of the hidden layers. The length of the list defines
                                       the number of hidden layers, and each element specifies the
                                       size of a layer.

        """
        super().__init__(input_dim, output_dim)

        self.hidden_layers = hidden_layers

        dims = [self.input_dim, *hidden_layers, self.output_dim]
        layers = []
        for i in range(len(dims) - 1):
            layers.append(nn.Linear(dims[i], dims[i + 1]))
            if i < len(dims) - 2:
                layers.append(nn.ReLU())

        self.model = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Perform a forward pass.

        Args:
            x (torch.Tensor): Input tensor.

        Returns:
            torch.Tensor: Output tensor.

        """
        return self.model(x)
