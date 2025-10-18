from collections.abc import Mapping
from typing import (
    TYPE_CHECKING,
    Any,
    TypeVar,
)

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.streamer_status import StreamerStatus

if TYPE_CHECKING:
    from ..models.streamer_token import StreamerToken


T = TypeVar("T", bound="Streamer")


@_attrs_define
class Streamer:
    """Describes streamer status

    Attributes:
        id (str): Assigned streamer id
        status (StreamerStatus):
        token (StreamerToken): Token for authorizing broadcaster streamer connection
    """

    id: str
    status: StreamerStatus
    token: "StreamerToken"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        status = self.status.value

        token = self.token.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "status": status,
                "token": token,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.streamer_token import StreamerToken

        d = dict(src_dict)
        id = d.pop("id")

        status = StreamerStatus(d.pop("status"))

        token = StreamerToken.from_dict(d.pop("token"))

        streamer = cls(
            id=id,
            status=status,
            token=token,
        )

        streamer.additional_properties = d
        return streamer

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
