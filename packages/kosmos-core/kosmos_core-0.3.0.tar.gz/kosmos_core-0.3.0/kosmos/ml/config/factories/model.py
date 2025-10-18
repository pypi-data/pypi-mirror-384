from abc import ABC, abstractmethod

from kosmos.ml.config.factories.encoding import EncodingConfig
from kosmos.ml.models.model import Model
from kosmos.ml.models.neural_network import NeuralNetwork
from kosmos.ml.models.vqc.vqc import VQC
from kosmos.ml.typing import TensorMapping


class ModelConfig(ABC):
    """Model configuration."""

    @abstractmethod
    def get_instance(self, input_dim: int, output_dim: int) -> Model:
        """Get the model instance.

        Args:
            input_dim (int): Model input dimension.
            output_dim (int): Model output dimension.

        Returns:
            Model: Model instance.

        """


class NeuralNetworkConfig(ModelConfig):
    """Neural network configuration."""

    def __init__(self, hidden_layers: list[int]) -> None:
        """Initialize the neural network configuration.

        Args:
            hidden_layers (list[int]): Sizes of the hidden layers. The length of the list defines
                                       the number of hidden layers, and each element specifies the
                                       size of a layer.

        """
        if not all(isinstance(h, int) and h > 0 for h in hidden_layers):
            msg = "hidden_layers must be a list of positive integers."
            raise ValueError(msg)

        self.hidden_layers = hidden_layers

    def get_instance(self, input_dim: int, output_dim: int) -> NeuralNetwork:
        """Get the neural network instance.

        Args:
            input_dim (int): Model input dimension.
            output_dim (int): Model output dimension.

        Returns:
            NeuralNetwork: Neural network instance.

        """
        return NeuralNetwork(input_dim, output_dim, self.hidden_layers)


class VQCConfig(ModelConfig):
    """Variational quantum circuit configuration."""

    def __init__(  # noqa: PLR0913
        self,
        num_layers: int,
        encoding_config: EncodingConfig,
        weight_mapping_func: TensorMapping | None = None,
        input_mapping_func: TensorMapping | None = None,
        weight_init_range: tuple[float, float] = (-1.0, 1.0),
        bias_init_range: tuple[float, float] | None = (-0.001, 0.001),
        *,
        data_reuploading: bool = False,
        output_scaling: bool = False,
    ) -> None:
        """Initialize the VQC configuration.

        Args:
            num_layers (int): The number of variational layers.
            encoding_config (EncodingConfig): The encoding configuration.
            weight_mapping_func (TensorMapping | None): The mapping function for the weights.
                                                        Defaults to None.
            input_mapping_func (TensorMapping | None): The mapping function for the input.
                                                       Defaults to None.
            weight_init_range (tuple[float, float]): Lower and upper bounds for initializing the
                trainable weight parameters. Defaults to (-1.0, 1.0).
            bias_init_range (tuple[float, float] | None): Lower and upper bounds for initializing
                the trainable bias parameters applied to each output unit. If None, no bias
                parameters are used. Defaults to (-0.001, 0.001).
            data_reuploading (bool): Whether to use data re-uploading. Defaults to False.
            output_scaling (bool): Whether to use output scaling. Defaults to False.

        """
        if num_layers < 1:
            msg = "num_layers must be >= 1."
            raise ValueError(msg)

        self.num_layers = num_layers
        self.encoding_config = encoding_config
        self.weight_mapping_func = weight_mapping_func
        self.input_mapping_func = input_mapping_func
        self.weight_init_range = weight_init_range
        self.bias_init_range = bias_init_range
        self.data_reuploading = data_reuploading
        self.output_scaling = output_scaling

    def get_instance(self, input_dim: int, output_dim: int) -> VQC:
        """Get the VQC instance.

        Args:
            input_dim (int): Model input dimension.
            output_dim (int): Model output dimension.

        Returns:
            VQC: VQC instance.

        """
        return VQC(
            input_dim=input_dim,
            output_dim=output_dim,
            num_layers=self.num_layers,
            encoding_config=self.encoding_config,
            weight_mapping_func=self.weight_mapping_func,
            input_mapping_func=self.input_mapping_func,
            weight_init_range=self.weight_init_range,
            bias_init_range=self.bias_init_range,
            data_reuploading=self.data_reuploading,
            output_scaling=self.output_scaling,
        )
