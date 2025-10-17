from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.on_call_role_relationship_data_type_0_type import (
    OnCallRoleRelationshipDataType0Type,
    check_on_call_role_relationship_data_type_0_type,
)
from ..types import UNSET, Unset

T = TypeVar("T", bound="OnCallRoleRelationshipDataType0")


@_attrs_define
class OnCallRoleRelationshipDataType0:
    """
    Attributes:
        id (Union[Unset, str]):
        type_ (Union[Unset, OnCallRoleRelationshipDataType0Type]):
    """

    id: Union[Unset, str] = UNSET
    type_: Union[Unset, OnCallRoleRelationshipDataType0Type] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        type_: Union[Unset, str] = UNSET
        if not isinstance(self.type_, Unset):
            type_ = self.type_

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if type_ is not UNSET:
            field_dict["type"] = type_

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id", UNSET)

        _type_ = d.pop("type", UNSET)
        type_: Union[Unset, OnCallRoleRelationshipDataType0Type]
        if isinstance(_type_, Unset):
            type_ = UNSET
        else:
            type_ = check_on_call_role_relationship_data_type_0_type(_type_)

        on_call_role_relationship_data_type_0 = cls(
            id=id,
            type_=type_,
        )

        on_call_role_relationship_data_type_0.additional_properties = d
        return on_call_role_relationship_data_type_0

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
