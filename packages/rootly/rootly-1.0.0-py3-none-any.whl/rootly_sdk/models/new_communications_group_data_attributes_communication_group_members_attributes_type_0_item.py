from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="NewCommunicationsGroupDataAttributesCommunicationGroupMembersAttributesType0Item")


@_attrs_define
class NewCommunicationsGroupDataAttributesCommunicationGroupMembersAttributesType0Item:
    """
    Attributes:
        user_id (Union[Unset, int]): User ID
    """

    user_id: Union[Unset, int] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        user_id = self.user_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if user_id is not UNSET:
            field_dict["user_id"] = user_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        user_id = d.pop("user_id", UNSET)

        new_communications_group_data_attributes_communication_group_members_attributes_type_0_item = cls(
            user_id=user_id,
        )

        new_communications_group_data_attributes_communication_group_members_attributes_type_0_item.additional_properties = d
        return new_communications_group_data_attributes_communication_group_members_attributes_type_0_item

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
