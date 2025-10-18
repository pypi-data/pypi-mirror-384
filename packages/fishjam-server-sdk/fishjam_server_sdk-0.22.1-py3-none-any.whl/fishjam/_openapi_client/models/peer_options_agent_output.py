from collections.abc import Mapping
from typing import (
    Any,
    TypeVar,
    Union,
)

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.peer_options_agent_output_audio_format import (
    PeerOptionsAgentOutputAudioFormat,
)
from ..models.peer_options_agent_output_audio_sample_rate import (
    PeerOptionsAgentOutputAudioSampleRate,
)
from ..types import UNSET, Unset

T = TypeVar("T", bound="PeerOptionsAgentOutput")


@_attrs_define
class PeerOptionsAgentOutput:
    """Output audio options

    Attributes:
        audio_format (Union[Unset, PeerOptionsAgentOutputAudioFormat]): The format of the output audio Default:
            PeerOptionsAgentOutputAudioFormat.PCM16. Example: pcm16.
        audio_sample_rate (Union[Unset, PeerOptionsAgentOutputAudioSampleRate]): The sample rate of the output audio
            Default: PeerOptionsAgentOutputAudioSampleRate.VALUE_16000. Example: 16000.
    """

    audio_format: Union[
        Unset, PeerOptionsAgentOutputAudioFormat
    ] = PeerOptionsAgentOutputAudioFormat.PCM16
    audio_sample_rate: Union[
        Unset, PeerOptionsAgentOutputAudioSampleRate
    ] = PeerOptionsAgentOutputAudioSampleRate.VALUE_16000
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        audio_format: Union[Unset, str] = UNSET
        if not isinstance(self.audio_format, Unset):
            audio_format = self.audio_format.value

        audio_sample_rate: Union[Unset, int] = UNSET
        if not isinstance(self.audio_sample_rate, Unset):
            audio_sample_rate = self.audio_sample_rate.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if audio_format is not UNSET:
            field_dict["audioFormat"] = audio_format
        if audio_sample_rate is not UNSET:
            field_dict["audioSampleRate"] = audio_sample_rate

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        _audio_format = d.pop("audioFormat", UNSET)
        audio_format: Union[Unset, PeerOptionsAgentOutputAudioFormat]
        if isinstance(_audio_format, Unset):
            audio_format = UNSET
        else:
            audio_format = PeerOptionsAgentOutputAudioFormat(_audio_format)

        _audio_sample_rate = d.pop("audioSampleRate", UNSET)
        audio_sample_rate: Union[Unset, PeerOptionsAgentOutputAudioSampleRate]
        if isinstance(_audio_sample_rate, Unset):
            audio_sample_rate = UNSET
        else:
            audio_sample_rate = PeerOptionsAgentOutputAudioSampleRate(
                _audio_sample_rate
            )

        peer_options_agent_output = cls(
            audio_format=audio_format,
            audio_sample_rate=audio_sample_rate,
        )

        peer_options_agent_output.additional_properties = d
        return peer_options_agent_output

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
