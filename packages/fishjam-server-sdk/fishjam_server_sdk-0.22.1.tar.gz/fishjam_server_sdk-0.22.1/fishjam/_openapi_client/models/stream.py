from collections.abc import Mapping
from typing import (
    TYPE_CHECKING,
    Any,
    TypeVar,
    Union,
)

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.streamer import Streamer
    from ..models.viewer import Viewer


T = TypeVar("T", bound="Stream")


@_attrs_define
class Stream:
    """Describes stream status

    Attributes:
        id (str): Assigned stream id
        public (bool):
        streamers (list['Streamer']): List of all streamers
        viewers (list['Viewer']): List of all viewers
        audio_only (Union[Unset, bool]): True if stream is restricted to audio only
    """

    id: str
    public: bool
    streamers: list["Streamer"]
    viewers: list["Viewer"]
    audio_only: Union[Unset, bool] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        public = self.public

        streamers = []
        for streamers_item_data in self.streamers:
            streamers_item = streamers_item_data.to_dict()
            streamers.append(streamers_item)

        viewers = []
        for viewers_item_data in self.viewers:
            viewers_item = viewers_item_data.to_dict()
            viewers.append(viewers_item)

        audio_only = self.audio_only

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "public": public,
                "streamers": streamers,
                "viewers": viewers,
            }
        )
        if audio_only is not UNSET:
            field_dict["audioOnly"] = audio_only

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.streamer import Streamer
        from ..models.viewer import Viewer

        d = dict(src_dict)
        id = d.pop("id")

        public = d.pop("public")

        streamers = []
        _streamers = d.pop("streamers")
        for streamers_item_data in _streamers:
            streamers_item = Streamer.from_dict(streamers_item_data)

            streamers.append(streamers_item)

        viewers = []
        _viewers = d.pop("viewers")
        for viewers_item_data in _viewers:
            viewers_item = Viewer.from_dict(viewers_item_data)

            viewers.append(viewers_item)

        audio_only = d.pop("audioOnly", UNSET)

        stream = cls(
            id=id,
            public=public,
            streamers=streamers,
            viewers=viewers,
            audio_only=audio_only,
        )

        stream.additional_properties = d
        return stream

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
