from enum import Enum


class StreamerStatus(str, Enum):
    """None"""

    CONNECTED = "connected"
    DISCONNECTED = "disconnected"

    def __str__(self) -> str:
        return str(self.value)
