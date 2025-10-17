from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.communications_group_communication_group_conditions_type_0_item_property_type import (
    CommunicationsGroupCommunicationGroupConditionsType0ItemPropertyType,
)
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.communications_group_communication_group_conditions_type_0_item_properties_type_0_item import (
        CommunicationsGroupCommunicationGroupConditionsType0ItemPropertiesType0Item,
    )


T = TypeVar("T", bound="CommunicationsGroupCommunicationGroupConditionsType0Item")


@_attrs_define
class CommunicationsGroupCommunicationGroupConditionsType0Item:
    """
    Attributes:
        id (Union[Unset, str]): ID of the condition
        condition (Union[Unset, str]): Condition
        property_type (Union[Unset, CommunicationsGroupCommunicationGroupConditionsType0ItemPropertyType]): Property
            type
        properties (Union[None, Unset,
            list['CommunicationsGroupCommunicationGroupConditionsType0ItemPropertiesType0Item']]): Properties
    """

    id: Union[Unset, str] = UNSET
    condition: Union[Unset, str] = UNSET
    property_type: Union[Unset, CommunicationsGroupCommunicationGroupConditionsType0ItemPropertyType] = UNSET
    properties: Union[
        None, Unset, list["CommunicationsGroupCommunicationGroupConditionsType0ItemPropertiesType0Item"]
    ] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        condition = self.condition

        property_type: Union[Unset, str] = UNSET
        if not isinstance(self.property_type, Unset):
            property_type = self.property_type.value

        properties: Union[None, Unset, list[dict[str, Any]]]
        if isinstance(self.properties, Unset):
            properties = UNSET
        elif isinstance(self.properties, list):
            properties = []
            for properties_type_0_item_data in self.properties:
                properties_type_0_item = properties_type_0_item_data.to_dict()
                properties.append(properties_type_0_item)

        else:
            properties = self.properties

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if condition is not UNSET:
            field_dict["condition"] = condition
        if property_type is not UNSET:
            field_dict["property_type"] = property_type
        if properties is not UNSET:
            field_dict["properties"] = properties

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        from ..models.communications_group_communication_group_conditions_type_0_item_properties_type_0_item import (
            CommunicationsGroupCommunicationGroupConditionsType0ItemPropertiesType0Item,
        )

        d = src_dict.copy()
        id = d.pop("id", UNSET)

        condition = d.pop("condition", UNSET)

        _property_type = d.pop("property_type", UNSET)
        property_type: Union[Unset, CommunicationsGroupCommunicationGroupConditionsType0ItemPropertyType]
        if isinstance(_property_type, Unset):
            property_type = UNSET
        else:
            property_type = CommunicationsGroupCommunicationGroupConditionsType0ItemPropertyType(_property_type)

        def _parse_properties(
            data: object,
        ) -> Union[None, Unset, list["CommunicationsGroupCommunicationGroupConditionsType0ItemPropertiesType0Item"]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                properties_type_0 = []
                _properties_type_0 = data
                for properties_type_0_item_data in _properties_type_0:
                    properties_type_0_item = (
                        CommunicationsGroupCommunicationGroupConditionsType0ItemPropertiesType0Item.from_dict(
                            properties_type_0_item_data
                        )
                    )

                    properties_type_0.append(properties_type_0_item)

                return properties_type_0
            except:  # noqa: E722
                pass
            return cast(
                Union[None, Unset, list["CommunicationsGroupCommunicationGroupConditionsType0ItemPropertiesType0Item"]],
                data,
            )

        properties = _parse_properties(d.pop("properties", UNSET))

        communications_group_communication_group_conditions_type_0_item = cls(
            id=id,
            condition=condition,
            property_type=property_type,
            properties=properties,
        )

        communications_group_communication_group_conditions_type_0_item.additional_properties = d
        return communications_group_communication_group_conditions_type_0_item

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
