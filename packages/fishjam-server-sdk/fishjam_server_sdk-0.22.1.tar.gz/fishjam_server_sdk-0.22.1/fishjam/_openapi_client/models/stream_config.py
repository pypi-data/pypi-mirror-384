from collections.abc import Mapping
from typing import (
    Any,
    TypeVar,
    Union,
    cast,
)

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="StreamConfig")


@_attrs_define
class StreamConfig:
    """Stream configuration

    Attributes:
        audio_only (Union[None, Unset, bool]): Restrics stream to audio only Default: False.
        public (Union[Unset, bool]): True if livestream viewers can omit specifying a token. Default: False.
    """

    audio_only: Union[None, Unset, bool] = False
    public: Union[Unset, bool] = False
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        audio_only: Union[None, Unset, bool]
        if isinstance(self.audio_only, Unset):
            audio_only = UNSET
        else:
            audio_only = self.audio_only

        public = self.public

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if audio_only is not UNSET:
            field_dict["audioOnly"] = audio_only
        if public is not UNSET:
            field_dict["public"] = public

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_audio_only(data: object) -> Union[None, Unset, bool]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, bool], data)

        audio_only = _parse_audio_only(d.pop("audioOnly", UNSET))

        public = d.pop("public", UNSET)

        stream_config = cls(
            audio_only=audio_only,
            public=public,
        )

        stream_config.additional_properties = d
        return stream_config

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
