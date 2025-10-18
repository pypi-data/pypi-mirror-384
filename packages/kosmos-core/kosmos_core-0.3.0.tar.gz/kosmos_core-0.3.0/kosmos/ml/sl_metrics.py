from dataclasses import dataclass

from numpy import ndarray
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score


@dataclass(frozen=True)
class SLMetrics:
    """Supervised learning classification evaluation metrics.

    Attributes:
        accuracy (float): Overall classification accuracy.
        precision (float): Weighted average precision across classes.
        recall (float): Weighted average recall across classes.
        f1 (float): Weighted average F1 score across classes.

    """

    accuracy: float
    precision: float
    recall: float
    f1: float

    def __str__(self) -> str:
        """Return a human-readable string with all metrics formatted to four decimals."""
        return (
            f"Accuracy: {self.accuracy:.4f} | "
            f"Precision: {self.precision:.4f} | "
            f"Recall: {self.recall:.4f} | "
            f"F1: {self.f1:.4f}"
        )


def calculate_sl_metrics(y_true: ndarray, y_pred: ndarray) -> SLMetrics:
    """Calculate supervised learning classification metrics for a given prediction.

    Args:
        y_true (ndarray): Ground-truth labels.
        y_pred (ndarray): Predicted labels.

    Returns:
        SLMetrics: Evaluation metrics.

    """
    return SLMetrics(
        accuracy=accuracy_score(y_true, y_pred),
        precision=precision_score(y_true, y_pred, average="weighted", zero_division=0),
        recall=recall_score(y_true, y_pred, average="weighted", zero_division=0),
        f1=f1_score(y_true, y_pred, average="weighted", zero_division=0),
    )
