from kosmos.topology.net import Network
from kosmos.utils.rng import RNG


class Simulator:
    """Base class for simulators."""

    def __init__(self, network: Network, seed: int = 1) -> None:
        """Initialize the simulator.

        Args:
            network (Network): The network topology.
            seed (int): The seed for the random number generator. Defaults to 1.

        """
        self.network = network
        self.seed = seed

        RNG.initialize(seed)
