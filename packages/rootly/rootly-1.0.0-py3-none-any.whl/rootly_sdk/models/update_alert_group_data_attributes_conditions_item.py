from typing import Any, TypeVar, Union, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.update_alert_group_data_attributes_conditions_item_conditionable_type import (
    UpdateAlertGroupDataAttributesConditionsItemConditionableType,
)
from ..models.update_alert_group_data_attributes_conditions_item_property_field_condition_type import (
    UpdateAlertGroupDataAttributesConditionsItemPropertyFieldConditionType,
)
from ..models.update_alert_group_data_attributes_conditions_item_property_field_type import (
    UpdateAlertGroupDataAttributesConditionsItemPropertyFieldType,
)
from ..types import UNSET, Unset

T = TypeVar("T", bound="UpdateAlertGroupDataAttributesConditionsItem")


@_attrs_define
class UpdateAlertGroupDataAttributesConditionsItem:
    """
    Attributes:
        property_field_type (UpdateAlertGroupDataAttributesConditionsItemPropertyFieldType): The type of the property
            field
        property_field_condition_type (UpdateAlertGroupDataAttributesConditionsItemPropertyFieldConditionType): The
            condition type of the property field
        id (Union[Unset, UUID]): The ID of the alert group condition
        property_field_name (Union[Unset, str]): The name of the property field. If the property field type is selected
            as 'attribute', then the allowed property field names are 'summary' (for Title), 'description', 'alert_urgency'
            and 'external_url' (for Alert Source URL). If the property field type is selected as 'payload', then the
            property field name should be supplied in JSON Path syntax.
        property_field_value (Union[Unset, str]): The value of the property field. Can be null if the property field
            condition type is 'is_one_of' or 'is_not_one_of'
        property_field_values (Union[Unset, list[str]]): The values of the property field. Need to be passed if the
            property field condition type is 'is_one_of' or 'is_not_one_of' except for when property field name is
            'alert_urgency'
        alert_urgency_ids (Union[None, Unset, list[str]]): The Alert Urgency ID's to check in the condition. Only need
            to be set when the property field type is 'attribute', the property field name is 'alert_urgency' and the
            property field condition type is 'is_one_of' or 'is_not_one_of'
        conditionable_type (Union[Unset, UpdateAlertGroupDataAttributesConditionsItemConditionableType]): The type of
            the conditionable
        conditionable_id (Union[Unset, str]): The ID of the conditionable. If conditionable_type is AlertField, this is
            the ID of the alert field.
    """

    property_field_type: UpdateAlertGroupDataAttributesConditionsItemPropertyFieldType
    property_field_condition_type: UpdateAlertGroupDataAttributesConditionsItemPropertyFieldConditionType
    id: Union[Unset, UUID] = UNSET
    property_field_name: Union[Unset, str] = UNSET
    property_field_value: Union[Unset, str] = UNSET
    property_field_values: Union[Unset, list[str]] = UNSET
    alert_urgency_ids: Union[None, Unset, list[str]] = UNSET
    conditionable_type: Union[Unset, UpdateAlertGroupDataAttributesConditionsItemConditionableType] = UNSET
    conditionable_id: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        property_field_type = self.property_field_type.value

        property_field_condition_type = self.property_field_condition_type.value

        id: Union[Unset, str] = UNSET
        if not isinstance(self.id, Unset):
            id = str(self.id)

        property_field_name = self.property_field_name

        property_field_value = self.property_field_value

        property_field_values: Union[Unset, list[str]] = UNSET
        if not isinstance(self.property_field_values, Unset):
            property_field_values = self.property_field_values

        alert_urgency_ids: Union[None, Unset, list[str]]
        if isinstance(self.alert_urgency_ids, Unset):
            alert_urgency_ids = UNSET
        elif isinstance(self.alert_urgency_ids, list):
            alert_urgency_ids = self.alert_urgency_ids

        else:
            alert_urgency_ids = self.alert_urgency_ids

        conditionable_type: Union[Unset, str] = UNSET
        if not isinstance(self.conditionable_type, Unset):
            conditionable_type = self.conditionable_type.value

        conditionable_id = self.conditionable_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "property_field_type": property_field_type,
                "property_field_condition_type": property_field_condition_type,
            }
        )
        if id is not UNSET:
            field_dict["id"] = id
        if property_field_name is not UNSET:
            field_dict["property_field_name"] = property_field_name
        if property_field_value is not UNSET:
            field_dict["property_field_value"] = property_field_value
        if property_field_values is not UNSET:
            field_dict["property_field_values"] = property_field_values
        if alert_urgency_ids is not UNSET:
            field_dict["alert_urgency_ids"] = alert_urgency_ids
        if conditionable_type is not UNSET:
            field_dict["conditionable_type"] = conditionable_type
        if conditionable_id is not UNSET:
            field_dict["conditionable_id"] = conditionable_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        property_field_type = UpdateAlertGroupDataAttributesConditionsItemPropertyFieldType(
            d.pop("property_field_type")
        )

        property_field_condition_type = UpdateAlertGroupDataAttributesConditionsItemPropertyFieldConditionType(
            d.pop("property_field_condition_type")
        )

        _id = d.pop("id", UNSET)
        id: Union[Unset, UUID]
        if isinstance(_id, Unset):
            id = UNSET
        else:
            id = UUID(_id)

        property_field_name = d.pop("property_field_name", UNSET)

        property_field_value = d.pop("property_field_value", UNSET)

        property_field_values = cast(list[str], d.pop("property_field_values", UNSET))

        def _parse_alert_urgency_ids(data: object) -> Union[None, Unset, list[str]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                alert_urgency_ids_type_0 = cast(list[str], data)

                return alert_urgency_ids_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list[str]], data)

        alert_urgency_ids = _parse_alert_urgency_ids(d.pop("alert_urgency_ids", UNSET))

        _conditionable_type = d.pop("conditionable_type", UNSET)
        conditionable_type: Union[Unset, UpdateAlertGroupDataAttributesConditionsItemConditionableType]
        if isinstance(_conditionable_type, Unset):
            conditionable_type = UNSET
        else:
            conditionable_type = UpdateAlertGroupDataAttributesConditionsItemConditionableType(_conditionable_type)

        conditionable_id = d.pop("conditionable_id", UNSET)

        update_alert_group_data_attributes_conditions_item = cls(
            property_field_type=property_field_type,
            property_field_condition_type=property_field_condition_type,
            id=id,
            property_field_name=property_field_name,
            property_field_value=property_field_value,
            property_field_values=property_field_values,
            alert_urgency_ids=alert_urgency_ids,
            conditionable_type=conditionable_type,
            conditionable_id=conditionable_id,
        )

        update_alert_group_data_attributes_conditions_item.additional_properties = d
        return update_alert_group_data_attributes_conditions_item

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
