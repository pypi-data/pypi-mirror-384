from importlib.resources import files

import numpy as np

from kosmos.ml.datasets.dataset import SLDataset


class IrisDataset(SLDataset):
    """Iris dataset for multiclass classification.

    Notes:
        - Number of instances: 150 (50 per class)
        - Number of features: 4 numeric
        - Classes: 3 (balanced; ~33.3% each)

    References:
        - UCI Machine Learning Repository — Iris dataset: https://archive.ics.uci.edu/dataset/53/iris

    """

    def __init__(self, *, min_max_scaler: bool = True) -> None:
        """Initialize the dataset.

        Args:
            min_max_scaler (bool): Whether to apply min-max scaling to the features.

        """
        with (files("kosmos.ml.datasets.data") / "iris.data").open("r", encoding="utf-8") as f:
            data = np.loadtxt(f)
        x = data[:, :-1]
        y = data[:, -1]
        super().__init__(x, y, min_max_scaler=min_max_scaler)

    @property
    def class_names(self) -> list[str]:
        """Return human-readable class labels: 0 -> setosa, 1 -> versicolor, 2 -> virginica."""
        return ["setosa", "versicolor", "virginica"]
