import torch
from torch import nn

from kosmos.ml.config.factories.encoding import EncodingConfig
from kosmos.ml.models.model import Model
from kosmos.ml.models.vqc.circuit import ParameterizedCircuit
from kosmos.ml.typing import TensorMapping


class VQC(Model):
    """Variational quantum circuit."""

    def __init__(  # noqa: PLR0913
        self,
        input_dim: int,
        output_dim: int,
        num_layers: int,
        encoding_config: EncodingConfig,
        weight_mapping_func: TensorMapping | None,
        input_mapping_func: TensorMapping | None,
        weight_init_range: tuple[float, float],
        bias_init_range: tuple[float, float] | None,
        *,
        data_reuploading: bool,
        output_scaling: bool,
    ) -> None:
        """Initialize the VQC.

        Args:
            input_dim (int): The input dimension of the model.
            output_dim (int): The output dimension of the model.
            num_layers (int): The number of variational layers.
            encoding_config (EncodingConfig): The encoding configuration.
            weight_mapping_func (TensorMapping | None): The mapping function for the weights.
            input_mapping_func (TensorMapping | None): The mapping function for the input.
            weight_init_range (tuple[float, float]): Lower and upper bounds for initializing the
                                                     trainable weight parameters.
            bias_init_range (tuple[float, float] | None): Lower and upper bounds for initializing
                the trainable bias parameters applied to each output unit. If None, no bias
                parameters are used.
            data_reuploading (bool): Whether to use data re-uploading.
            output_scaling (bool): Whether to use output scaling.

        """
        super().__init__(input_dim, output_dim)

        self.num_layers = num_layers
        self.weight_mapping_func = weight_mapping_func or (lambda x: x)
        self.input_mapping_func = input_mapping_func or (lambda x: x)

        self.data_reuploading = data_reuploading
        self.output_scaling = output_scaling

        self.encoding = encoding_config.get_instance(self.input_dim, self.output_dim)
        self.circuit = ParameterizedCircuit(
            self.encoding, self.num_layers, data_reuploading=self.data_reuploading
        )

        self.num_qubits = self.encoding.num_qubits

        # Trainable parameters
        init_min, init_max = weight_init_range
        self.weights = nn.Parameter(
            torch.empty(self.num_layers, self.num_qubits, 3, dtype=torch.float32).uniform_(
                init_min, init_max
            )
        )

        if bias_init_range is not None:
            init_min, init_max = bias_init_range
            self.bias = nn.Parameter(
                torch.empty(self.output_dim, dtype=torch.float32).uniform_(init_min, init_max)
            )
        else:
            self.bias = None

        self.output_scaling_parameter = (
            nn.Parameter(torch.ones(1, dtype=torch.float32)) if self.output_scaling else None
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Perform a forward pass.

        Args:
            x (torch.Tensor): Input tensor.

        Returns:
            torch.Tensor: Output tensor.

        """
        outputs = []

        mapped_weights = self.weight_mapping_func(self.weights)

        for model_input in x:
            mapped_input = self.input_mapping_func(model_input)
            circuit_out = self.circuit.expect_z(mapped_weights, mapped_input)
            outputs.append(circuit_out.to(torch.float32))

        output = torch.stack(outputs)

        if self.output_scaling_parameter is not None:
            output = self.output_scaling_parameter * output

        if self.bias is not None:
            output = output + self.bias

        return output
