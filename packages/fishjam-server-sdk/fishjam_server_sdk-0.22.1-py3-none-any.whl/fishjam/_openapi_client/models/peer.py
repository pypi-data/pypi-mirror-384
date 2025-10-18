from collections.abc import Mapping
from typing import (
    TYPE_CHECKING,
    Any,
    TypeVar,
    Union,
    cast,
)

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.peer_status import PeerStatus
from ..models.peer_type import PeerType
from ..models.subscribe_mode import SubscribeMode

if TYPE_CHECKING:
    from ..models.peer_metadata import PeerMetadata
    from ..models.track import Track


T = TypeVar("T", bound="Peer")


@_attrs_define
class Peer:
    """Describes peer status

    Attributes:
        id (str): Assigned peer id Example: 4a1c1164-5fb7-425d-89d7-24cdb8fff1cf.
        metadata (Union['PeerMetadata', None]): Custom metadata set by the peer Example: {'name': 'FishjamUser'}.
        status (PeerStatus): Informs about the peer status Example: disconnected.
        subscribe_mode (SubscribeMode): Configuration of peer's subscribing policy
        subscriptions (list[str]): Describes peer's subscriptions in manual mode
        tracks (list['Track']): List of all peer's tracks
        type_ (PeerType): Peer type Example: webrtc.
    """

    id: str
    metadata: Union["PeerMetadata", None]
    status: PeerStatus
    subscribe_mode: SubscribeMode
    subscriptions: list[str]
    tracks: list["Track"]
    type_: PeerType
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.peer_metadata import PeerMetadata

        id = self.id

        metadata: Union[None, dict[str, Any]]
        if isinstance(self.metadata, PeerMetadata):
            metadata = self.metadata.to_dict()
        else:
            metadata = self.metadata

        status = self.status.value

        subscribe_mode = self.subscribe_mode.value

        subscriptions = self.subscriptions

        tracks = []
        for tracks_item_data in self.tracks:
            tracks_item = tracks_item_data.to_dict()
            tracks.append(tracks_item)

        type_ = self.type_.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "metadata": metadata,
                "status": status,
                "subscribeMode": subscribe_mode,
                "subscriptions": subscriptions,
                "tracks": tracks,
                "type": type_,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.peer_metadata import PeerMetadata
        from ..models.track import Track

        d = dict(src_dict)
        id = d.pop("id")

        def _parse_metadata(data: object) -> Union["PeerMetadata", None]:
            if data is None:
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_peer_metadata_type_0 = PeerMetadata.from_dict(data)

                return componentsschemas_peer_metadata_type_0
            except:  # noqa: E722
                pass
            return cast(Union["PeerMetadata", None], data)

        metadata = _parse_metadata(d.pop("metadata"))

        status = PeerStatus(d.pop("status"))

        subscribe_mode = SubscribeMode(d.pop("subscribeMode"))

        subscriptions = cast(list[str], d.pop("subscriptions"))

        tracks = []
        _tracks = d.pop("tracks")
        for tracks_item_data in _tracks:
            tracks_item = Track.from_dict(tracks_item_data)

            tracks.append(tracks_item)

        type_ = PeerType(d.pop("type"))

        peer = cls(
            id=id,
            metadata=metadata,
            status=status,
            subscribe_mode=subscribe_mode,
            subscriptions=subscriptions,
            tracks=tracks,
            type_=type_,
        )

        peer.additional_properties = d
        return peer

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
