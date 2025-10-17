from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="CommunicationsGroupCommunicationGroupConditionsType0ItemPropertiesType0Item")


@_attrs_define
class CommunicationsGroupCommunicationGroupConditionsType0ItemPropertiesType0Item:
    """
    Attributes:
        name (Union[Unset, str]):
        id (Union[Unset, str]):
    """

    name: Union[Unset, str] = UNSET
    id: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        id = self.id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if name is not UNSET:
            field_dict["name"] = name
        if id is not UNSET:
            field_dict["id"] = id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        name = d.pop("name", UNSET)

        id = d.pop("id", UNSET)

        communications_group_communication_group_conditions_type_0_item_properties_type_0_item = cls(
            name=name,
            id=id,
        )

        communications_group_communication_group_conditions_type_0_item_properties_type_0_item.additional_properties = d
        return communications_group_communication_group_conditions_type_0_item_properties_type_0_item

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
