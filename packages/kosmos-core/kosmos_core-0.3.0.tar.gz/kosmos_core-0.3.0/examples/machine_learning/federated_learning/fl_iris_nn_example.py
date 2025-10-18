from kosmos.ml.config.factories.loss import CrossEntropyLossConfig
from kosmos.ml.config.factories.lr_scheduler import CosineLearningRateSchedulerConfig
from kosmos.ml.config.factories.model import NeuralNetworkConfig
from kosmos.ml.config.factories.optimizer import AdamOptimizerConfig
from kosmos.ml.config.sl_train import FLTrainConfig
from kosmos.ml.datasets.iris_dataset import IrisDataset
from kosmos.simulator.fl_simulator import FLSimulator
from kosmos.topology.link import ClassicalLink, LinkId
from kosmos.topology.net import Network
from kosmos.topology.node import ClassicalNode, NodeId, NodeRole


def construct_network() -> Network:
    """Construct network topology with two classical clients and one classical server."""
    network = Network()

    # Create classical nodes (clients and server)
    client_node_1 = ClassicalNode(
        id=NodeId("client_1"),
        roles=[NodeRole.END_USER],
    )
    client_node_2 = ClassicalNode(
        id=NodeId("client_2"),
        roles=[NodeRole.END_USER],
    )
    server_node = ClassicalNode(
        id=NodeId("server"),
        roles=[NodeRole.END_USER],
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


def fl_iris_nn_example() -> None:
    """Run example of federated training and testing on the Iris dataset using a neural network."""
    network = construct_network()

    # Dataset to train and test on
    dataset = IrisDataset()

    # Model configuration that defines the neural network to use
    nn_config = NeuralNetworkConfig([16, 16])

    # Configure federated learning
    train_config = FLTrainConfig(
        dataset=dataset,
        train_split=0.7,
        batch_size=8,
        num_epochs=5,
        model_config=nn_config,
        optimizer_config=AdamOptimizerConfig(lr=0.01),
        lr_scheduler_config=CosineLearningRateSchedulerConfig(max_epochs=5),
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
    fl_iris_nn_example()
