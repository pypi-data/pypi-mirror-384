from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.alert_group_conditions_item_property_field_condition_type import (
    AlertGroupConditionsItemPropertyFieldConditionType,
)
from ..models.alert_group_conditions_item_property_field_type import AlertGroupConditionsItemPropertyFieldType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.alert_group_conditions_item_values_item_type_0 import AlertGroupConditionsItemValuesItemType0


T = TypeVar("T", bound="AlertGroupConditionsItem")


@_attrs_define
class AlertGroupConditionsItem:
    """
    Attributes:
        property_field_type (AlertGroupConditionsItemPropertyFieldType): The type of the property field
        property_field_condition_type (AlertGroupConditionsItemPropertyFieldConditionType): The condition type of the
            property field
        property_field_name (Union[None, Unset, str]): The name of the property field. If the property field type is
            selected as 'attribute', then the allowed property field names are 'summary' (for Title), 'description',
            'alert_urgency' and 'external_url' (for Alert Source URL). If the property field type is selected as 'payload',
            then the property field name should be supplied in JSON Path syntax.
        property_field_value (Union[None, Unset, str]): The value of the property field. Can be null if the property
            field condition type is 'is_one_of' or 'is_not_one_of'
        property_field_values (Union[Unset, list[str]]): The values of the property field. Used if the property field
            condition type is 'is_one_of' or 'is_not_one_of' except for when property field name is 'alert_urgency'
        values (Union[Unset, list[Union['AlertGroupConditionsItemValuesItemType0', None]]]):
    """

    property_field_type: AlertGroupConditionsItemPropertyFieldType
    property_field_condition_type: AlertGroupConditionsItemPropertyFieldConditionType
    property_field_name: Union[None, Unset, str] = UNSET
    property_field_value: Union[None, Unset, str] = UNSET
    property_field_values: Union[Unset, list[str]] = UNSET
    values: Union[Unset, list[Union["AlertGroupConditionsItemValuesItemType0", None]]] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.alert_group_conditions_item_values_item_type_0 import AlertGroupConditionsItemValuesItemType0

        property_field_type = self.property_field_type.value

        property_field_condition_type = self.property_field_condition_type.value

        property_field_name: Union[None, Unset, str]
        if isinstance(self.property_field_name, Unset):
            property_field_name = UNSET
        else:
            property_field_name = self.property_field_name

        property_field_value: Union[None, Unset, str]
        if isinstance(self.property_field_value, Unset):
            property_field_value = UNSET
        else:
            property_field_value = self.property_field_value

        property_field_values: Union[Unset, list[str]] = UNSET
        if not isinstance(self.property_field_values, Unset):
            property_field_values = self.property_field_values

        values: Union[Unset, list[Union[None, dict[str, Any]]]] = UNSET
        if not isinstance(self.values, Unset):
            values = []
            for values_item_data in self.values:
                values_item: Union[None, dict[str, Any]]
                if isinstance(values_item_data, AlertGroupConditionsItemValuesItemType0):
                    values_item = values_item_data.to_dict()
                else:
                    values_item = values_item_data
                values.append(values_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "property_field_type": property_field_type,
                "property_field_condition_type": property_field_condition_type,
            }
        )
        if property_field_name is not UNSET:
            field_dict["property_field_name"] = property_field_name
        if property_field_value is not UNSET:
            field_dict["property_field_value"] = property_field_value
        if property_field_values is not UNSET:
            field_dict["property_field_values"] = property_field_values
        if values is not UNSET:
            field_dict["values"] = values

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        from ..models.alert_group_conditions_item_values_item_type_0 import AlertGroupConditionsItemValuesItemType0

        d = src_dict.copy()
        property_field_type = AlertGroupConditionsItemPropertyFieldType(d.pop("property_field_type"))

        property_field_condition_type = AlertGroupConditionsItemPropertyFieldConditionType(
            d.pop("property_field_condition_type")
        )

        def _parse_property_field_name(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        property_field_name = _parse_property_field_name(d.pop("property_field_name", UNSET))

        def _parse_property_field_value(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        property_field_value = _parse_property_field_value(d.pop("property_field_value", UNSET))

        property_field_values = cast(list[str], d.pop("property_field_values", UNSET))

        values = []
        _values = d.pop("values", UNSET)
        for values_item_data in _values or []:

            def _parse_values_item(data: object) -> Union["AlertGroupConditionsItemValuesItemType0", None]:
                if data is None:
                    return data
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    values_item_type_0 = AlertGroupConditionsItemValuesItemType0.from_dict(data)

                    return values_item_type_0
                except:  # noqa: E722
                    pass
                return cast(Union["AlertGroupConditionsItemValuesItemType0", None], data)

            values_item = _parse_values_item(values_item_data)

            values.append(values_item)

        alert_group_conditions_item = cls(
            property_field_type=property_field_type,
            property_field_condition_type=property_field_condition_type,
            property_field_name=property_field_name,
            property_field_value=property_field_value,
            property_field_values=property_field_values,
            values=values,
        )

        alert_group_conditions_item.additional_properties = d
        return alert_group_conditions_item

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
