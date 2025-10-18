import gzip
from importlib.resources import as_file, files
from typing import ClassVar

import numpy as np

from kosmos.ml.datasets.dataset import SLDataset


class FashionDataset(SLDataset):
    """Fashion MNIST dataset for multiclass classification.

    Notes:
      - Number of instances: 70,000 (60,000 train + 10,000 test)
      - Number of features: 784 numeric (28x28 pixel images, flattened)
      - Classes: 10 (balanced; clothing categories: T-shirt/top, Trouser, Pullover,
          Dress, Coat, Sandal, Shirt, Sneaker, Bag, Ankle boot)

    References:
      - OpenML — Fashion-MNIST dataset: https://www.openml.org/d/40996

    """

    CLASSES: ClassVar[list[str]] = [
        "T-shirt/top",
        "Trouser",
        "Pullover",
        "Dress",
        "Coat",
        "Sandal",
        "Shirt",
        "Sneaker",
        "Bag",
        "Ankle boot",
    ]

    def __init__(self, *, min_max_scaler: bool = True) -> None:
        """Initialize the dataset.

        Args:
            min_max_scaler (bool): Whether to apply min-max scaling to the features.

        """
        path = files("kosmos.ml.datasets.data") / "fashion_mnist.data.gz"
        with as_file(path) as p, gzip.open(p, mode="r") as f:
            data = np.loadtxt((line.decode("utf-8") for line in f), delimiter=",")

        x = data[:, :-1].astype(np.float32, copy=False)
        y = data[:, -1].astype(np.int64, copy=False)

        super().__init__(x, y, min_max_scaler=min_max_scaler)

    @property
    def class_names(self) -> list[str]:
        """Return human-readable class labels of clothing categories."""
        return self.CLASSES
