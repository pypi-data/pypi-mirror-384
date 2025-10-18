from kosmos.protocols.config.protocol import RoutingProtocolConfig
from kosmos.protocols.routing.dijkstra_routing import DijkstraRoutingProtocol
from kosmos.topology.link import ClassicalLink, LinkId, LinkType, OpticalLink, QuantumLink
from kosmos.topology.net import Network
from kosmos.topology.node import ClassicalNode, NodeId, NodeRole, QuantumNode

NODES = [
    ("A", ClassicalNode, {"roles": [NodeRole.END_USER]}),
    ("QB", QuantumNode, {"roles": [NodeRole.ROUTER], "num_qubits": 10, "coherence_time": 1.0}),
    ("C", ClassicalNode, {"roles": [NodeRole.ROUTER]}),
    ("D", ClassicalNode, {"roles": [NodeRole.ROUTER]}),
    ("QE", QuantumNode, {"roles": [NodeRole.END_USER], "num_qubits": 5, "coherence_time": 0.5}),
    ("F", ClassicalNode, {"roles": [NodeRole.ROUTER]}),
]

LINKS = [
    ("AB", "A", "QB", ClassicalLink, {"distance": 10000.0, "bandwidth": 1e9}),
    ("AC", "A", "C", ClassicalLink, {"distance": 5000.0, "bandwidth": 1e9}),
    ("AD", "A", "D", ClassicalLink, {"distance": 15000.0, "bandwidth": 1e9}),
    ("CD", "C", "D", ClassicalLink, {"distance": 8000.0, "bandwidth": 1e9}),
    ("DF", "D", "F", ClassicalLink, {"distance": 12000.0, "bandwidth": 1e9}),
    ("EF", "QE", "F", ClassicalLink, {"distance": 900000.0, "bandwidth": 1e9}),
    ("QBE", "QB", "QE", QuantumLink, {"distance": 2000.0, "repetition_rate": 1e6}),
]


def create_example_network() -> Network:
    """Create an example network."""
    network = Network()
    nodes = {}

    # Create nodes
    for node_id, node_class, params in NODES:
        defaults = {"has_transceiver": True} if node_class == QuantumNode else {}
        node = node_class(id=NodeId(node_id), **defaults, **params)
        network.add_node(node)
        nodes[node_id] = node

    # Create links
    for link_id, src_id, dst_id, link_class, params in LINKS:
        defaults = {"attenuation": 0.0002, "signal_speed": 200.0}
        if link_class == QuantumLink:
            defaults["polarization_fidelity"] = 0.99
        link = link_class(
            id=LinkId(link_id), src=nodes[src_id], dst=nodes[dst_id], **defaults, **params
        )
        network.add_link(link)

    return network


def main() -> None:
    """Run Dijkstra routing protocol example."""
    network = create_example_network()

    # Run Dijkstra from A to QE
    source, target = network.get_node("A"), network.get_node("QE")

    config_cost = RoutingProtocolConfig(
        allowed_link_types=[LinkType.QUANTUM, LinkType.CLASSICAL], cost_function="cost"
    )
    result_cost = DijkstraRoutingProtocol(config_cost, network, source, target).execute()

    config_distance = RoutingProtocolConfig(
        allowed_link_types=[LinkType.QUANTUM, LinkType.CLASSICAL], cost_function="distance"
    )
    result_distance = DijkstraRoutingProtocol(config_distance, network, source, target).execute()

    output = ["\n=== Nodes ==="]
    output.extend(f"{node.id}: {node.__class__.__name__}" for node in network.nodes())

    output.append("\n=== Links ===")
    for link in network.links():
        if not isinstance(link, OpticalLink):
            msg = "Only optical links are supported."
            raise TypeError(msg)
        output.append(
            f"{link.id}: {link.src.id} <--> {link.dst.id} ({link.__class__.__name__}); "
            f"Dist: {link.distance:.4f}, Cost: {link.weight:.4g}"
        )

    output.append("\n=== Dijkstra Routing (by Cost) ===")
    output.append(str(result_cost))

    output.append("\n=== Dijkstra Routing (by Distance) ===")
    output.append(str(result_distance))

    print("\n".join(output))  # noqa: T201


if __name__ == "__main__":
    main()
