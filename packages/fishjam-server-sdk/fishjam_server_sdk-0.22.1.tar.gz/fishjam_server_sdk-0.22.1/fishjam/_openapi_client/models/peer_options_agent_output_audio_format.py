from enum import Enum


class PeerOptionsAgentOutputAudioFormat(str, Enum):
    """The format of the output audio"""

    PCM16 = "pcm16"

    def __str__(self) -> str:
        return str(self.value)
