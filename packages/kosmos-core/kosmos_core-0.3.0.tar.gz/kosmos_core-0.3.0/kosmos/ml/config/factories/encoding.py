from abc import ABC, abstractmethod
from typing import Literal

from kosmos.ml.models.vqc.encoding import AmplitudeEmbedding, AngleEmbedding, VQCEncoding


class EncodingConfig(ABC):
    """Encoding configuration."""

    @abstractmethod
    def get_instance(self, input_dim: int, output_dim: int) -> VQCEncoding:
        """Get the encoding instance.

        Args:
            input_dim (int): Model input dimension.
            output_dim (int): Model output dimension.

        Returns:
            VQCEncoding: Encoding instance.

        """


class AngleEmbeddingConfig(EncodingConfig):
    """Angle embedding configuration."""

    def __init__(self, rotation: Literal["X", "Y", "Z"] = "X") -> None:
        """Initialize the angle embedding configuration.

        Args:
            rotation (Literal["X", "Y", "Z"]): The rotation to use for the angle embedding.
                                               Defaults to "X".

        """
        self.rotation = rotation

    def get_instance(self, input_dim: int, output_dim: int) -> AngleEmbedding:
        """Get the angle embedding instance.

        Args:
            input_dim (int): Model input dimension.
            output_dim (int): Model output dimension.

        Returns:
            AngleEmbedding: Angle embedding instance.

        """
        return AngleEmbedding(input_dim, output_dim, self.rotation)


class AmplitudeEmbeddingConfig(EncodingConfig):
    """Amplitude embedding configuration."""

    def __init__(self, pad_with: complex = 0.3, *, normalize: bool = True) -> None:
        """Initialize the amplitude embedding configuration.

        Args:
            pad_with (complex): The input is padded with this constant to size :math:`2^n`.
            normalize (bool): Whether to normalize the features. Defaults to True.

        """
        self.pad_with = pad_with
        self.normalize = normalize

    def get_instance(self, input_dim: int, output_dim: int) -> AmplitudeEmbedding:
        """Get the amplitude embedding instance.

        Args:
            input_dim (int): Model input dimension.
            output_dim (int): Model output dimension.

        Returns:
            AmplitudeEmbedding: Amplitude embedding instance.

        """
        return AmplitudeEmbedding(input_dim, output_dim, self.pad_with, normalize=self.normalize)
