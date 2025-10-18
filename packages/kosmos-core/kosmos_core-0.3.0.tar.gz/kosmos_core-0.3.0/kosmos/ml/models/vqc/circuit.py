import pennylane as qml
import torch
from pennylane.measurements import ExpectationMP

from kosmos.ml.models.vqc.encoding import VQCEncoding


class ParameterizedCircuit:
    """Parameterized quantum circuit using PennyLane with statevector simulation."""

    def __init__(
        self,
        encoding: VQCEncoding,
        num_layers: int,
        *,
        data_reuploading: bool,
    ) -> None:
        """Initialize the circuit.

        Args:
            encoding (VQCEncoding): The VQC encoding.
            num_layers (int): The number of variational layers.
            data_reuploading (bool): Whether to use data re-uploading.

        """
        self.encoding = encoding
        self.num_qubits = self.encoding.num_qubits
        self.output_dim = self.encoding.output_dim

        self.num_layers = num_layers
        self.data_reuploading = data_reuploading

        self.device = qml.device("lightning.qubit", wires=self.num_qubits)
        self.qnode = qml.QNode(self._circuit, self.device, interface="torch")

    def _circuit(self, weights: torch.Tensor, x: torch.Tensor) -> list[ExpectationMP]:
        """Circuit definition.

        Args:
            weights (torch.Tensor): Weights tensor.
            x (torch.Tensor): Input tensor.

        Returns:
            list[ExpectationMP]: List of Z-expectation measurement processes.

        """
        if not self.data_reuploading:
            self.encoding.apply_operation(x, wires=range(self.num_qubits))

        for w in weights:
            if self.data_reuploading:
                self.encoding.apply_operation(x, wires=range(self.num_qubits))
            qml.StronglyEntanglingLayers(w.unsqueeze(0), wires=range(self.num_qubits))

        return [qml.expval(qml.PauliZ(i)) for i in range(self.output_dim)]

    def expect_z(self, weights: torch.Tensor, x: torch.Tensor) -> torch.Tensor:
        """Execute the circuit and calculate Z expectation values.

        Args:
            weights (torch.Tensor): Weights tensor.
            x (torch.Tensor): Input tensor.

        Returns:
            torch.Tensor: Z expectation values.

        """
        return qml.math.stack(self.qnode(weights, x))
