from importlib.resources import files
from typing import ClassVar

import numpy as np
import pandas as pd

from kosmos.ml.datasets.dataset import SLDataset


class IncomeDataset(SLDataset):
    """Adult Income (Census) dataset — binary classification (>50K vs <=50K).

    Notes:
        - Instances: 48,842 (32,561 train + 16,281 test)
        - Features: 14 (Mix numerical and categorical), after One-Hot-Decision more columns
        - Classes: 2 (imbalanced; ~24% >50K, ~76% <=50K)

    References:
        - UCI ML Repository — Adult
          https://archive.ics.uci.edu/ml/machine-learning-databases/adult/

    """

    COLS: ClassVar[list[str]] = [
        "age",
        "workclass",
        "fnlwgt",
        "education",
        "education_num",
        "marital_status",
        "occupation",
        "relationship",
        "race",
        "sex",
        "capital_gain",
        "capital_loss",
        "hours_per_week",
        "native_country",
        "income",
    ]

    def __init__(self, *, min_max_scaler: bool = True) -> None:
        """Initialize the dataset.

        Args:
            min_max_scaler (bool): Whether to apply min-max scaling to the features.

        """
        with (files("kosmos.ml.datasets.data") / "adult.data").open("r", encoding="utf-8") as f:
            df = pd.read_csv(
                f,
                header=None,
                names=self.COLS,
                sep=",",
                skipinitialspace=True,
                na_values="?",
            )

        df["income"] = (
            df["income"]
            .astype(str)
            .str.strip()
            .str.replace(".", "", regex=False)
            .map({">50K": 1, "<=50K": 0})
            .astype("Int64")
        )

        y = df["income"].astype("int64").to_numpy()

        x = df.drop(columns=["income"])

        # One-Hot-Encoding
        cat_cols = x.select_dtypes(include=["object"]).columns.tolist()
        x = pd.get_dummies(x, columns=cat_cols, drop_first=True)

        # Set missing values to 0
        x = x.fillna(0)

        x = x.to_numpy(dtype=np.float32)

        super().__init__(x, y, min_max_scaler=min_max_scaler)

    @property
    def class_names(self) -> list[str]:
        """Return human-readable class labels: 0 -> <=50K, 1 -> >50K."""
        return ["<=50K", ">50K"]
