from abc import ABC, abstractmethod
from collections.abc import Collection

import numpy as np
import torch
from sklearn.preprocessing import MinMaxScaler
from torch import Tensor
from torch.utils.data import Dataset


class SLDataset(Dataset[tuple[Tensor, Tensor]], ABC):
    """Dataset for supervised learning classification."""

    def __init__(self, x: Collection, y: Collection, *, min_max_scaler: bool = True) -> None:
        """Initialize the dataset.

        Args:
            x (Collection): Feature values.
            y (Collection): Target values.
            min_max_scaler (bool): Whether to apply min-max scaling to the features.

        """
        x = np.asarray(x, dtype=np.float32)
        y = np.asarray(y, dtype=np.float32)
        if min_max_scaler:
            x = MinMaxScaler().fit_transform(x)
        self.x = torch.from_numpy(x)
        self.y = torch.from_numpy(y)

    def __len__(self) -> int:
        """Return the total number of samples."""
        return self.x.shape[0]

    def __getitem__(self, index: int) -> tuple[Tensor, Tensor]:
        """Return a (features, target) pair for the given index."""
        return self.x[index], self.y[index]

    @property
    def input_dimension(self) -> int:
        """Number of feature columns."""
        return self.x.shape[1]

    @property
    def output_dim(self) -> int:
        """Number of distinct classes."""
        return int(self.y.unique().numel())

    @property
    @abstractmethod
    def class_names(self) -> list[str]:
        """Class names."""
