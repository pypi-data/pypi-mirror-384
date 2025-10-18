from abc import ABC, abstractmethod

from kosmos.protocols.config.protocol import ProtocolConfig
from kosmos.protocols.protocol_result import ProtocolResult
from kosmos.protocols.status import ProtocolStatus
from kosmos.topology.net import Network


class Protocol(ABC):
    """Base class for all protocols."""

    def __init__(self, config: ProtocolConfig, network: Network) -> None:
        """Initialize the protocol.

        Args:
            config (ProtocolConfig): Protocol configuration.
            network (Network): The network topology.

        """
        self.config = config
        self.network = network

        self.status = ProtocolStatus.INITIALIZED

    @abstractmethod
    def execute(self) -> ProtocolResult:
        """Execute the protocol.

        Returns:
            ProtocolResult: Result of the protocol execution.

        """
