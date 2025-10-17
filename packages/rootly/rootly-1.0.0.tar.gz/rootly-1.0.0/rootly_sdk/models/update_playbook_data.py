from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.update_playbook_data_type import UpdatePlaybookDataType

if TYPE_CHECKING:
    from ..models.update_playbook_data_attributes import UpdatePlaybookDataAttributes


T = TypeVar("T", bound="UpdatePlaybookData")


@_attrs_define
class UpdatePlaybookData:
    """
    Attributes:
        type_ (UpdatePlaybookDataType):
        attributes (UpdatePlaybookDataAttributes):
    """

    type_: UpdatePlaybookDataType
    attributes: "UpdatePlaybookDataAttributes"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        type_ = self.type_.value

        attributes = self.attributes.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "type": type_,
                "attributes": attributes,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        from ..models.update_playbook_data_attributes import UpdatePlaybookDataAttributes

        d = src_dict.copy()
        type_ = UpdatePlaybookDataType(d.pop("type"))

        attributes = UpdatePlaybookDataAttributes.from_dict(d.pop("attributes"))

        update_playbook_data = cls(
            type_=type_,
            attributes=attributes,
        )

        update_playbook_data.additional_properties = d
        return update_playbook_data

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
