import torch

from kosmos.ml.config.factories.encoding import AngleEmbeddingConfig
from kosmos.ml.config.factories.loss import CrossEntropyLossConfig
from kosmos.ml.config.factories.model import VQCConfig
from kosmos.ml.config.factories.optimizer import AdamOptimizerConfig
from kosmos.ml.config.sl_train import FLTrainConfig
from kosmos.ml.datasets.iris_dataset import IrisDataset
from kosmos.simulator.fl_simulator import FLSimulator
from kosmos.topology.link import ClassicalLink, LinkId
from kosmos.topology.net import Network
from kosmos.topology.node import NodeId, NodeRole, QuantumNode


def construct_network() -> Network:
    """Construct network topology with two quantum clients and one quantum server."""
    network = Network()

    # Create quantum nodes (clients and server)
    client_node_1 = QuantumNode(
        id=NodeId("client_1"),
        roles=[NodeRole.END_USER],
        num_qubits=127,
        coherence_time=4.0e-04,
    )
    client_node_2 = QuantumNode(
        id=NodeId("client_2"),
        roles=[NodeRole.END_USER],
        num_qubits=127,
        coherence_time=4.0e-04,
    )
    server_node = QuantumNode(
        id=NodeId("server"),
        roles=[NodeRole.END_USER],
        num_qubits=127,
        coherence_time=4.0e-04,
    )

    # Create classical links connecting clients to the server
    client_server_link_1 = ClassicalLink(
        id=LinkId("c1_server"),
        src=client_node_1,
        dst=server_node,
        distance=1000.0,
        attenuation=0.0002,
        signal_speed=0.0002,
        bandwidth=10e9,
    )
    client_server_link_2 = ClassicalLink(
        id=LinkId("c2_server"),
        src=client_node_2,
        dst=server_node,
        distance=1000.0,
        attenuation=0.0002,
        signal_speed=0.0002,
        bandwidth=10e9,
    )

    # Add nodes and links to the network
    network.add_node(client_node_1)
    network.add_node(client_node_2)
    network.add_node(server_node)
    network.add_link(client_server_link_1)
    network.add_link(client_server_link_2)

    return network


def fl_iris_vqc_example() -> None:
    """Run example of federated training and testing on the Iris dataset using a VQC."""
    network = construct_network()

    # Dataset to train and test on
    dataset = IrisDataset()

    # Model configuration that defines the variational quantum circuit to use
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

    # Configure federated learning
    train_config = FLTrainConfig(
        dataset=dataset,
        train_split=0.7,
        batch_size=8,
        num_epochs=5,
        model_config=vqc_config,
        optimizer_config=AdamOptimizerConfig(lr=0.01),
        lr_scheduler_config=None,
        max_grad_norm=1.0,
        loss_config=CrossEntropyLossConfig(),
        num_rounds=5,
    )

    # Initialize simulator, which is responsible for running the federated learning experiment
    simulator = FLSimulator(
        network,
        train_config,
        client_nodes=["client_1", "client_2"],
        server_node="server",
        seed=1,
    )

    # Run training
    for epoch_result in simulator.train():
        print(epoch_result)  # noqa: T201

    # Evaluate trained model
    print(simulator.test())  # noqa: T201


if __name__ == "__main__":
    fl_iris_vqc_example()
