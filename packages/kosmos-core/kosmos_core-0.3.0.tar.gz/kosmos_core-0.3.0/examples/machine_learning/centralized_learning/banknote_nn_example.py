from kosmos.ml.cl_manager import CLManager
from kosmos.ml.config.factories.loss import CrossEntropyLossConfig
from kosmos.ml.config.factories.lr_scheduler import CosineLearningRateSchedulerConfig
from kosmos.ml.config.factories.model import NeuralNetworkConfig
from kosmos.ml.config.factories.optimizer import AdamOptimizerConfig
from kosmos.ml.config.sl_train import SLTrainConfig
from kosmos.ml.datasets.banknote_dataset import BanknoteDataset
from kosmos.utils.rng import RNG


def banknote_nn_example() -> None:
    """Run example of training and testing on the Banknote dataset using a neural network."""
    RNG.initialize(seed=1)

    banknote_dataset = BanknoteDataset()

    config = SLTrainConfig(
        dataset=banknote_dataset,
        train_split=0.7,
        batch_size=32,
        num_epochs=50,
        model_config=NeuralNetworkConfig([16, 16]),
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
    banknote_nn_example()
