from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="CommunicationsGroupCommunicationGroupMembersType0Item")


@_attrs_define
class CommunicationsGroupCommunicationGroupMembersType0Item:
    """
    Attributes:
        id (Union[Unset, str]): ID of the group member
        user_id (Union[Unset, int]): User ID
        name (Union[Unset, str]): Name of the group member
        email (Union[Unset, str]): Email of the group member
    """

    id: Union[Unset, str] = UNSET
    user_id: Union[Unset, int] = UNSET
    name: Union[Unset, str] = UNSET
    email: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        user_id = self.user_id

        name = self.name

        email = self.email

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if user_id is not UNSET:
            field_dict["user_id"] = user_id
        if name is not UNSET:
            field_dict["name"] = name
        if email is not UNSET:
            field_dict["email"] = email

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id", UNSET)

        user_id = d.pop("user_id", UNSET)

        name = d.pop("name", UNSET)

        email = d.pop("email", UNSET)

        communications_group_communication_group_members_type_0_item = cls(
            id=id,
            user_id=user_id,
            name=name,
            email=email,
        )

        communications_group_communication_group_members_type_0_item.additional_properties = d
        return communications_group_communication_group_members_type_0_item

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
