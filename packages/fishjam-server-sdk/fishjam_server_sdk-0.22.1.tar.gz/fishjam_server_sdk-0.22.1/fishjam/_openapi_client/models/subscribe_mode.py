from enum import Enum


class SubscribeMode(str, Enum):
    """Configuration of peer's subscribing policy"""

    AUTO = "auto"
    MANUAL = "manual"

    def __str__(self) -> str:
        return str(self.value)
