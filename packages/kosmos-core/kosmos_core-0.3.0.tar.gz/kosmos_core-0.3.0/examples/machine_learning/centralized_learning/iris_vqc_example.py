import torch

from kosmos.ml.cl_manager import CLManager
from kosmos.ml.config.factories.encoding import AngleEmbeddingConfig
from kosmos.ml.config.factories.loss import CrossEntropyLossConfig
from kosmos.ml.config.factories.model import VQCConfig
from kosmos.ml.config.factories.optimizer import AdamOptimizerConfig
from kosmos.ml.config.sl_train import SLTrainConfig
from kosmos.ml.datasets.iris_dataset import IrisDataset
from kosmos.utils.rng import RNG


def iris_vqc_example() -> None:
    """Run example of training and testing on the Iris dataset using a VQC."""
    RNG.initialize(seed=1)

    iris_dataset = IrisDataset()

    vqc_config = VQCConfig(
        num_layers=2,
        encoding_config=AngleEmbeddingConfig(rotation="X"),
        weight_mapping_func=lambda x: torch.pi * torch.tanh(x),
        input_mapping_func=lambda x: torch.pi * x,
        weight_init_range=(-1, 1),
        bias_init_range=(-0.001, 0.001),
        data_reuploading=True,
        output_scaling=True,
    )

    config = SLTrainConfig(
        dataset=iris_dataset,
        train_split=0.7,
        batch_size=8,
        num_epochs=50,
        model_config=vqc_config,
        optimizer_config=AdamOptimizerConfig(lr=0.01),
        lr_scheduler_config=None,
        max_grad_norm=1.0,
        loss_config=CrossEntropyLossConfig(),
    )

    manager = CLManager(config)

    for epoch_result in manager.train():
        print(epoch_result)  # noqa: T201
    print(manager.test())  # noqa: T201


if __name__ == "__main__":
    iris_vqc_example()
