from collections.abc import Iterator

import numpy as np
import torch
from torch.utils.data import DataLoader

from kosmos.ml.config.factories.loss import LossConfig
from kosmos.ml.config.factories.lr_scheduler import LearningRateSchedulerConfig
from kosmos.ml.config.factories.optimizer import OptimizerConfig
from kosmos.ml.models.model import Model
from kosmos.ml.sl_metrics import calculate_sl_metrics
from kosmos.ml.sl_result import SLTestIterationResult, SLTrainIterationResult
from kosmos.topology.node import Node

DEVICE = "cpu"


class SLTrainer:
    """Trainer for supervised learning classification tasks."""

    def __init__(
        self,
        model: Model,
        optimizer_config: OptimizerConfig,
        lr_scheduler_config: LearningRateSchedulerConfig | None,
        loss_config: LossConfig,
        max_grad_norm: float | None,
    ) -> None:
        """Initialize a supervised learning trainer.

        Args:
            model (Model): The model to train/evaluate.
            optimizer_config (OptimizerConfig): Optimizer configuration.
            lr_scheduler_config (LearningRateSchedulerConfig): Learning rate scheduler
                                                               configuration.
            loss_config (LossConfig): Loss configuration.
            max_grad_norm (float | None): Maximum gradient norm.

        """
        self.device = DEVICE

        self.model = model.to(self.device)

        self.optimizer = optimizer_config.get_instance(self.model.parameters())
        if lr_scheduler_config is not None:
            self.lr_scheduler = lr_scheduler_config.get_instance(self.optimizer)
        else:
            self.lr_scheduler = None
        self.criterion = loss_config.get_instance()
        self.max_grad_norm = max_grad_norm

    def train(
        self,
        num_epochs: int,
        dataloader: DataLoader,
        fl_round: int | None = None,
        node: Node | None = None,
    ) -> Iterator[SLTrainIterationResult]:
        """Train the model on the given train data.

        Args:
            num_epochs (int): Number of epochs to run.
            dataloader (DataLoader): DataLoader providing the train data.
            fl_round (int | None): Federated learning round index to attach to the results.
                                   Defaults to None.
            node (Node | None): Node corresponding to this iteration to attach to the results.
                                Defaults to None.

        Returns:
            Iterator[SLTrainIterationResult]: An iterator yielding one train result per epoch.

        """
        for epoch in range(num_epochs):
            result = self._train_epoch(epoch, dataloader)
            result.fl_round = fl_round
            result.node = node
            yield result

    def test(self, dataloader: DataLoader) -> SLTestIterationResult:
        """Evaluate the model on the given test dataloader.

        Args:
            dataloader (DataLoader): DataLoader providing the test data.

        Returns:
            SLTestIterationResult: Result of the test iteration.

        """
        return self._evaluate(dataloader)

    def _train_epoch(self, epoch: int, dataloader: DataLoader) -> SLTrainIterationResult:
        """Run a single training epoch.

        Args:
            epoch (int): The index of the epoch.
            dataloader (DataLoader): DataLoader providing the train data.

        Returns:
            SLTrainIterationResult: Result of the training iteration.

        """
        self.model.train()

        total_loss = 0.0
        all_preds, all_targets = [], []

        for batch in dataloader:
            x, y = batch
            x = x.to(self.device)
            y = y.to(self.device)

            self.optimizer.zero_grad(set_to_none=True)
            y_pred = self.model(x)

            batch_loss = self.criterion(y_pred, y.long())
            batch_loss.backward()
            if self.max_grad_norm is not None:
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), self.max_grad_norm)

            self.optimizer.step()

            total_loss += batch_loss.item()

            # Collect predictions and targets for metrics
            with torch.no_grad():
                all_preds.extend(y_pred.argmax(-1).cpu().tolist())
                all_targets.extend(y.long().cpu().tolist())

        if self.lr_scheduler:
            self.lr_scheduler.step()

        avg_loss = total_loss / len(dataloader)
        metrics = calculate_sl_metrics(
            y_true=np.asarray(all_targets),
            y_pred=np.asarray(all_preds),
        )

        return SLTrainIterationResult(avg_loss, metrics, epoch)

    def _evaluate(self, dataloader: DataLoader) -> SLTestIterationResult:
        """Run model evaluation.

        Args:
            dataloader (DataLoader): DataLoader providing the test data.

        Returns:
            SLTestIterationResult: Result of the test iteration.

        """
        self.model.eval()

        total_loss = 0.0
        all_preds, all_targets = [], []

        with torch.inference_mode():
            for batch in dataloader:
                x, y = batch
                x = x.to(self.device)
                y = y.to(self.device)

                y_pred = self.model(x)

                batch_loss = self.criterion(y_pred, y.long())
                total_loss += batch_loss.item()

                # Collect predictions and targets for metrics
                all_preds.extend(y_pred.argmax(-1).cpu().tolist())
                all_targets.extend(y.long().cpu().tolist())

        avg_loss = total_loss / len(dataloader)
        metrics = calculate_sl_metrics(
            y_true=np.asarray(all_targets),
            y_pred=np.asarray(all_preds),
        )

        return SLTestIterationResult(avg_loss, metrics)
