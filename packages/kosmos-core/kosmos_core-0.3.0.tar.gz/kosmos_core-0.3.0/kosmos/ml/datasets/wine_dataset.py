import numpy as np
from sklearn.datasets import load_wine

from kosmos.ml.datasets.dataset import SLDataset


class WineDataset(SLDataset):
    """Wine dataset for multiclass classification.

    Notes:
        - Number of instances: 178
        - Number of features: 13 numeric
        - Classes: 3 (slightly imbalanced;[59,71,48])

    References:
        - Scikit Learn Repository — Wine dataset: load_wine, dowloaded and fitted from https://archive.ics.uci.edu/ml/machine-learning-databases/wine/wine.data

    """

    def __init__(self, *, min_max_scaler: bool = True) -> None:
        """Initialize the dataset.

        Args:
            min_max_scaler (bool): Whether to apply min-max scaling to the features.

        """
        ds = load_wine()
        x = ds.data.astype(np.float32)
        y = ds.target.astype(np.int64)
        super().__init__(x, y, min_max_scaler=min_max_scaler)
        # Standard scaler?

    @property
    def class_names(self) -> list[str]:
        """Return human-readable class labels: class_0, class_1, class_2."""
        return ["class_0", "class_1", "class_2"]
