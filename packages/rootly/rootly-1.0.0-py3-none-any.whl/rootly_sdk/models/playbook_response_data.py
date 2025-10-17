from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.playbook_response_data_type import PlaybookResponseDataType

if TYPE_CHECKING:
    from ..models.playbook import Playbook


T = TypeVar("T", bound="PlaybookResponseData")


@_attrs_define
class PlaybookResponseData:
    """
    Attributes:
        id (str): Unique ID of the playbook
        type_ (PlaybookResponseDataType):
        attributes (Playbook):
    """

    id: str
    type_: PlaybookResponseDataType
    attributes: "Playbook"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        type_ = self.type_.value

        attributes = self.attributes.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "type": type_,
                "attributes": attributes,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        from ..models.playbook import Playbook

        d = src_dict.copy()
        id = d.pop("id")

        type_ = PlaybookResponseDataType(d.pop("type"))

        attributes = Playbook.from_dict(d.pop("attributes"))

        playbook_response_data = cls(
            id=id,
            type_=type_,
            attributes=attributes,
        )

        playbook_response_data.additional_properties = d
        return playbook_response_data

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
