from importlib.resources import files

import numpy as np

from kosmos.ml.datasets.dataset import SLDataset


class BanknoteDataset(SLDataset):
    """Banknote authentication dataset for binary classification.

    Notes:
        - Number of instances: 1372
        - Number of features: 4 numeric
        - Classes: 2 (slightly imbalanced; 762 real, 610 forged)

    References:
        - UCI Machine Learning Repository — Banknote authentication dataset: https://archive.ics.uci.edu/dataset/267/banknote+authentication

    """

    def __init__(self, *, min_max_scaler: bool = True) -> None:
        """Initialize the dataset.

        Args:
            min_max_scaler (bool): Whether to apply min-max scaling to the features.

        """
        with (files("kosmos.ml.datasets.data") / "banknote.data").open("r", encoding="utf-8") as f:
            data = np.loadtxt(f, delimiter=",")
        x = data[:, :-1]
        y = data[:, -1]
        super().__init__(x, y, min_max_scaler=min_max_scaler)

    @property
    def class_names(self) -> list[str]:
        """Return human-readable class labels: 0 = Genuine, 1 = Forged."""
        return ["Genuine", "Forged"]
