from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.custom_field_list_data_item_type import CustomFieldListDataItemType

if TYPE_CHECKING:
    from ..models.custom_field import CustomField


T = TypeVar("T", bound="CustomFieldListDataItem")


@_attrs_define
class CustomFieldListDataItem:
    """
    Attributes:
        id (str): Unique ID of the custom_field
        type_ (CustomFieldListDataItemType):
        attributes (CustomField):
    """

    id: str
    type_: CustomFieldListDataItemType
    attributes: "CustomField"
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
        from ..models.custom_field import CustomField

        d = src_dict.copy()
        id = d.pop("id")

        type_ = CustomFieldListDataItemType(d.pop("type"))

        attributes = CustomField.from_dict(d.pop("attributes"))

        custom_field_list_data_item = cls(
            id=id,
            type_=type_,
            attributes=attributes,
        )

        custom_field_list_data_item.additional_properties = d
        return custom_field_list_data_item

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
