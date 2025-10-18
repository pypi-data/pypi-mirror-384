import numpy as np
from sklearn.datasets import load_digits

from kosmos.ml.datasets.dataset import SLDataset


class DigitsDataset(SLDataset):
    """Digits dataset for multiclass classification.

    Notes:
        - Number of instances: 1797
        - Number of features: 64 numeric
        - Classes: 10 (roughly balanced, digits 0-9)

    References:
        - Scikit-Learn: Digits dataset (8x8 images of handwritten digits) https://scikit-learn.org/stable/modules/generated/sklearn.datasets.load_digits.html

    """

    def __init__(self, *, min_max_scaler: bool = True) -> None:
        """Initialize the dataset.

        Args:
            min_max_scaler (bool): Whether to apply min-max scaling to the features.

        """
        ds = load_digits()
        x = ds.data.astype(np.float32)
        y = ds.target.astype(np.int64)
        super().__init__(x, y, min_max_scaler=min_max_scaler)

    @property
    def class_names(self) -> list[str]:
        """Return human-readable class labels of numbers 0-9."""
        return [str(i) for i in range(10)]
