from kosmos.ml.cl_manager import CLManager
from kosmos.ml.config.factories.loss import CrossEntropyLossConfig
from kosmos.ml.config.factories.lr_scheduler import CosineLearningRateSchedulerConfig
from kosmos.ml.config.factories.model import NeuralNetworkConfig
from kosmos.ml.config.factories.optimizer import AdamOptimizerConfig
from kosmos.ml.config.sl_train import SLTrainConfig
from kosmos.ml.datasets.income_dataset import IncomeDataset
from kosmos.utils.rng import RNG


def income_nn_example() -> None:
    """Run example of training and testing on the Income dataset using a neural network."""
    RNG.initialize(seed=1)

    income_dataset = IncomeDataset()

    config = SLTrainConfig(
        dataset=income_dataset,
        train_split=0.7,
        batch_size=128,
        num_epochs=50,
        model_config=NeuralNetworkConfig([128, 64, 32]),
        optimizer_config=AdamOptimizerConfig(lr=1e-3),
        lr_scheduler_config=CosineLearningRateSchedulerConfig(max_epochs=50),
        max_grad_norm=1.0,
        loss_config=CrossEntropyLossConfig(),
    )

    manager = CLManager(config)

    for epoch_result in manager.train():
        print(epoch_result)  # noqa: T201
    print(manager.test())  # noqa: T201


if __name__ == "__main__":
    income_nn_example()
