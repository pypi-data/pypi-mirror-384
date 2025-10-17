from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.alerts_source_alert_source_urgency_rules_attributes_item_conditionable_type import (
    AlertsSourceAlertSourceUrgencyRulesAttributesItemConditionableType,
    check_alerts_source_alert_source_urgency_rules_attributes_item_conditionable_type,
)
from ..models.alerts_source_alert_source_urgency_rules_attributes_item_kind import (
    AlertsSourceAlertSourceUrgencyRulesAttributesItemKind,
    check_alerts_source_alert_source_urgency_rules_attributes_item_kind,
)
from ..models.alerts_source_alert_source_urgency_rules_attributes_item_operator import (
    AlertsSourceAlertSourceUrgencyRulesAttributesItemOperator,
    check_alerts_source_alert_source_urgency_rules_attributes_item_operator,
)
from ..types import UNSET, Unset

T = TypeVar("T", bound="AlertsSourceAlertSourceUrgencyRulesAttributesItem")


@_attrs_define
class AlertsSourceAlertSourceUrgencyRulesAttributesItem:
    """
    Attributes:
        json_path (Union[None, Unset, str]): JSON path expression to extract a specific value from the alert's payload
            for evaluation
        operator (Union[Unset, AlertsSourceAlertSourceUrgencyRulesAttributesItemOperator]): Comparison operator used to
            evaluate the extracted value against the specified condition
        value (Union[Unset, str]): Value that the extracted payload data is compared to using the specified operator to
            determine a match
        conditionable_type (Union[Unset, AlertsSourceAlertSourceUrgencyRulesAttributesItemConditionableType]): The type
            of the conditionable
        conditionable_id (Union[None, Unset, str]): The ID of the conditionable. If conditionable_type is AlertField,
            this is the ID of the alert field.
        kind (Union[Unset, AlertsSourceAlertSourceUrgencyRulesAttributesItemKind]): The kind of the conditionable
        alert_urgency_id (Union[Unset, str]): The ID of the alert urgency
    """

    json_path: Union[None, Unset, str] = UNSET
    operator: Union[Unset, AlertsSourceAlertSourceUrgencyRulesAttributesItemOperator] = UNSET
    value: Union[Unset, str] = UNSET
    conditionable_type: Union[Unset, AlertsSourceAlertSourceUrgencyRulesAttributesItemConditionableType] = UNSET
    conditionable_id: Union[None, Unset, str] = UNSET
    kind: Union[Unset, AlertsSourceAlertSourceUrgencyRulesAttributesItemKind] = UNSET
    alert_urgency_id: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        json_path: Union[None, Unset, str]
        if isinstance(self.json_path, Unset):
            json_path = UNSET
        else:
            json_path = self.json_path

        operator: Union[Unset, str] = UNSET
        if not isinstance(self.operator, Unset):
            operator = self.operator

        value = self.value

        conditionable_type: Union[Unset, str] = UNSET
        if not isinstance(self.conditionable_type, Unset):
            conditionable_type = self.conditionable_type

        conditionable_id: Union[None, Unset, str]
        if isinstance(self.conditionable_id, Unset):
            conditionable_id = UNSET
        else:
            conditionable_id = self.conditionable_id

        kind: Union[Unset, str] = UNSET
        if not isinstance(self.kind, Unset):
            kind = self.kind

        alert_urgency_id = self.alert_urgency_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if json_path is not UNSET:
            field_dict["json_path"] = json_path
        if operator is not UNSET:
            field_dict["operator"] = operator
        if value is not UNSET:
            field_dict["value"] = value
        if conditionable_type is not UNSET:
            field_dict["conditionable_type"] = conditionable_type
        if conditionable_id is not UNSET:
            field_dict["conditionable_id"] = conditionable_id
        if kind is not UNSET:
            field_dict["kind"] = kind
        if alert_urgency_id is not UNSET:
            field_dict["alert_urgency_id"] = alert_urgency_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_json_path(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        json_path = _parse_json_path(d.pop("json_path", UNSET))

        _operator = d.pop("operator", UNSET)
        operator: Union[Unset, AlertsSourceAlertSourceUrgencyRulesAttributesItemOperator]
        if isinstance(_operator, Unset):
            operator = UNSET
        else:
            operator = check_alerts_source_alert_source_urgency_rules_attributes_item_operator(_operator)

        value = d.pop("value", UNSET)

        _conditionable_type = d.pop("conditionable_type", UNSET)
        conditionable_type: Union[Unset, AlertsSourceAlertSourceUrgencyRulesAttributesItemConditionableType]
        if isinstance(_conditionable_type, Unset):
            conditionable_type = UNSET
        else:
            conditionable_type = check_alerts_source_alert_source_urgency_rules_attributes_item_conditionable_type(
                _conditionable_type
            )

        def _parse_conditionable_id(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        conditionable_id = _parse_conditionable_id(d.pop("conditionable_id", UNSET))

        _kind = d.pop("kind", UNSET)
        kind: Union[Unset, AlertsSourceAlertSourceUrgencyRulesAttributesItemKind]
        if isinstance(_kind, Unset):
            kind = UNSET
        else:
            kind = check_alerts_source_alert_source_urgency_rules_attributes_item_kind(_kind)

        alert_urgency_id = d.pop("alert_urgency_id", UNSET)

        alerts_source_alert_source_urgency_rules_attributes_item = cls(
            json_path=json_path,
            operator=operator,
            value=value,
            conditionable_type=conditionable_type,
            conditionable_id=conditionable_id,
            kind=kind,
            alert_urgency_id=alert_urgency_id,
        )

        alerts_source_alert_source_urgency_rules_attributes_item.additional_properties = d
        return alerts_source_alert_source_urgency_rules_attributes_item

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
