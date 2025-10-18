from importlib.resources import files

import numpy as np
import pandas as pd

from kosmos.ml.datasets.dataset import SLDataset


class QSARDataset(SLDataset):
    """QSAR biodegration dataset for binary classification.

    Notes:
        - Number of instances: 1055
        - Number of features: 41 numeric
        - Classes: 2 (slightly imbalanced, RD (ready biodegradable) ca 34%; NRB ca 66%)

    References:
        - UCI Machine Learning Repository — QSAR dataset: https://archive.ics.uci.edu/dataset/254/qsar+biodegradation

    """

    def __init__(self, *, min_max_scaler: bool = True) -> None:
        """Initialize the dataset.

        Args:
            min_max_scaler (bool): Whether to apply min-max scaling to the features.

        """
        with (files("kosmos.ml.datasets.data") / "qsar.data").open("r", encoding="utf-8") as f:
            df = pd.read_csv(f, sep=";", header=None)
        x = df.iloc[:, :-1].to_numpy(dtype=np.float32)
        y = (
            df.iloc[:, -1]
            .astype(str)
            .str.strip()
            .map({"NRB": 0, "RB": 1, "0": 0, "1": 1})
            .astype("int64")
            .to_numpy()
        )
        super().__init__(x, y, min_max_scaler=min_max_scaler)

    @property
    def class_names(self) -> list[str]:
        """Return human-readable class labels and map: NRB->0 (not ready biodegradable) RB->1."""
        return ["Not Ready Biodegradable", "Ready Biodegradable"]
