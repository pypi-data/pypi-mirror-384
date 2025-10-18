from importlib.resources import files

import numpy as np
import pandas as pd

from kosmos.ml.datasets.dataset import SLDataset


class WDBCDataset(SLDataset):
    """WDBC (wisconsin breast cancer) dataset for binary classification.

    Notes:
        - Number of instances: 569
        - Number of features: 30 numeric
        - Classes: 2 (slighty imbalanced; 357 benign, 212 malign)

    References:
        - UCI Machine Learning Repository — WDBC dataset: https://archive.ics.uci.edu/dataset/17/breast+cancer+wisconsin+diagnostic

    """

    def __init__(self, *, min_max_scaler: bool = True) -> None:
        """Initialize the dataset.

        Args:
            min_max_scaler (bool): Whether to apply min-max scaling to the features.

        """
        with (files("kosmos.ml.datasets.data") / "wdbc.data").open("r", encoding="utf-8") as f:
            cols = ["id", "diagnosis"] + [f"f{i}" for i in range(30)]
            df = pd.read_csv(f, header=None, names=cols)
        df = df.drop(columns=["id"])
        df["diagnosis"] = df["diagnosis"].map({"B": 0, "M": 1}).astype("int64")
        x = df.drop(columns=["diagnosis"]).to_numpy(np.float32)
        y = df["diagnosis"].to_numpy()
        super().__init__(x, y, min_max_scaler=min_max_scaler)

    @property
    def class_names(self) -> list[str]:
        """Return human-readable class labels and map: B->0 (Benign), M->1 (Malignant)."""
        return ["Benign", "Malignant"]
