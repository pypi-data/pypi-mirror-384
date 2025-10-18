from enum import Enum


class ProtocolStatus(Enum):
    """Status of a protocol."""

    INITIALIZED = "initialized"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
