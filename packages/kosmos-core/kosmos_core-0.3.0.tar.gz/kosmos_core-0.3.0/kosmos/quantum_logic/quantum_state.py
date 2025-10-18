import numpy as np
import scipy


class QuantumState:
    """Representation of a quantum state using a density matrix."""

    @staticmethod
    def validate_density_matrix(rho: np.ndarray, tolerance: float = 1e-10) -> None:
        """Verify whether the density matrix represents a quantum state.

        Args:
            rho (np.ndarray): Density matrix.
            tolerance (float): Tolerance due to inaccurate calculations. Defaults to 1e-10.

        """
        if rho.shape[0] != rho.shape[1]:
            msg = "Density matrix must be square."
            raise ValueError(msg)
        if not np.allclose(rho, rho.conj().T, atol=tolerance):
            msg = "Density matrix must be Hermitian."
            raise ValueError(msg)
        if not np.isclose(np.trace(rho), 1.0, atol=tolerance):
            msg = "Density matrix must have trace 1."
            raise ValueError(msg)
        if np.any(np.linalg.eigvalsh(rho) < -tolerance):
            msg = "Density matrix must be positive semidefinite."
            raise ValueError(msg)

    def __init__(
        self,
        *,
        creation_time: int | None = 0,
        rho: np.ndarray | None = None,
        fidelity: float | None = 0.0,
    ) -> None:
        """Initialize and validate density matrix and validity of state.

        Args:
            creation_time (int | None): Timestamp of creation. Defaults to 0.
            rho (np.ndarray | None): Density matrix of a quantum register. Defaults to None.
            fidelity (float | None): Fidelity value of a quantum register. Defaults to 0.0.

        """
        if fidelity > 1.0 or fidelity < 0.0:
            msg = "Fidelity must be a float between 0 and 1."
            raise ValueError(msg)

        if rho is not None:
            QuantumState.validate_density_matrix(rho)
            self._rho = rho
        else:
            # Default: |0><0|
            self._rho = np.zeros((2, 2), dtype=complex)
            self._rho[0, 0] = 1.0

        self.fidelity = fidelity
        self.creation_time = creation_time

    @property
    def rho(self) -> np.ndarray:
        """Density matrix of a state."""
        return self._rho

    @rho.setter
    def rho(self, density_matrix: np.ndarray) -> None:
        QuantumState.validate_density_matrix(density_matrix)
        self._rho = density_matrix

    @property
    def dim(self) -> int:
        """Dimension of rho."""
        return self._rho.shape[0]

    def fidelity_from_rho(self, target: "QuantumState") -> float:
        """Compute Uhlmann fidelity between two states.

        Args:
            target (QuantumState): target quantum state.

        Returns:
            float: Fidelity value between 0 and 1.

        """
        sqrt_rho = scipy.linalg.sqrtm(self._rho)  # d₁^(1/2) = √rho
        inner = sqrt_rho @ target.rho @ sqrt_rho  # d₁^(1/2) d₂ d₁^(1/2) = √rho sigma √rho
        s = scipy.linalg.sqrtm(inner)  # s = √(√rho sigma √rho)
        trace_s = np.trace(s)  # Sp s = Tr(s)
        return float(np.real(trace_s) ** 2)  # (Sp s)²

    def fidelity_with_target(self, target_rho: np.ndarray) -> float:
        """Compute fidelity between this state and an ideal target state.

        How close is the actual state to the ideal state.

        Args:
            target_rho (np.ndarray): Density matrix of the ideal target state.

        Returns:
            float: Fidelity value between 0 and 1:

        """
        target_state = QuantumState(rho=target_rho)
        return self.fidelity_from_rho(target_state)
