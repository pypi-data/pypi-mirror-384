from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.new_alerts_source_data_attributes_resolution_rule_attributes_conditions_attributes_item_conditionable_type import (
    NewAlertsSourceDataAttributesResolutionRuleAttributesConditionsAttributesItemConditionableType,
)
from ..models.new_alerts_source_data_attributes_resolution_rule_attributes_conditions_attributes_item_kind import (
    NewAlertsSourceDataAttributesResolutionRuleAttributesConditionsAttributesItemKind,
)
from ..models.new_alerts_source_data_attributes_resolution_rule_attributes_conditions_attributes_item_operator import (
    NewAlertsSourceDataAttributesResolutionRuleAttributesConditionsAttributesItemOperator,
)
from ..types import UNSET, Unset

T = TypeVar("T", bound="NewAlertsSourceDataAttributesResolutionRuleAttributesConditionsAttributesItem")


@_attrs_define
class NewAlertsSourceDataAttributesResolutionRuleAttributesConditionsAttributesItem:
    """
    Attributes:
        field (Union[Unset, str]): JSON path expression to extract a specific value from the alert's payload for
            evaluation
        operator (Union[Unset, NewAlertsSourceDataAttributesResolutionRuleAttributesConditionsAttributesItemOperator]):
            Comparison operator used to evaluate the extracted value against the specified condition
        value (Union[Unset, str]): Value that the extracted payload data is compared to using the specified operator to
            determine a match
        conditionable_type (Union[Unset,
            NewAlertsSourceDataAttributesResolutionRuleAttributesConditionsAttributesItemConditionableType]): The type of
            the conditionable
        conditionable_id (Union[Unset, str]): The ID of the conditionable. If conditionable_type is AlertField, this is
            the ID of the alert field.
        kind (Union[Unset, NewAlertsSourceDataAttributesResolutionRuleAttributesConditionsAttributesItemKind]): The kind
            of the conditionable
    """

    field: Union[Unset, str] = UNSET
    operator: Union[Unset, NewAlertsSourceDataAttributesResolutionRuleAttributesConditionsAttributesItemOperator] = (
        UNSET
    )
    value: Union[Unset, str] = UNSET
    conditionable_type: Union[
        Unset, NewAlertsSourceDataAttributesResolutionRuleAttributesConditionsAttributesItemConditionableType
    ] = UNSET
    conditionable_id: Union[Unset, str] = UNSET
    kind: Union[Unset, NewAlertsSourceDataAttributesResolutionRuleAttributesConditionsAttributesItemKind] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        field = self.field

        operator: Union[Unset, str] = UNSET
        if not isinstance(self.operator, Unset):
            operator = self.operator.value

        value = self.value

        conditionable_type: Union[Unset, str] = UNSET
        if not isinstance(self.conditionable_type, Unset):
            conditionable_type = self.conditionable_type.value

        conditionable_id = self.conditionable_id

        kind: Union[Unset, str] = UNSET
        if not isinstance(self.kind, Unset):
            kind = self.kind.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if field is not UNSET:
            field_dict["field"] = field
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

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        field = d.pop("field", UNSET)

        _operator = d.pop("operator", UNSET)
        operator: Union[Unset, NewAlertsSourceDataAttributesResolutionRuleAttributesConditionsAttributesItemOperator]
        if isinstance(_operator, Unset):
            operator = UNSET
        else:
            operator = NewAlertsSourceDataAttributesResolutionRuleAttributesConditionsAttributesItemOperator(_operator)

        value = d.pop("value", UNSET)

        _conditionable_type = d.pop("conditionable_type", UNSET)
        conditionable_type: Union[
            Unset, NewAlertsSourceDataAttributesResolutionRuleAttributesConditionsAttributesItemConditionableType
        ]
        if isinstance(_conditionable_type, Unset):
            conditionable_type = UNSET
        else:
            conditionable_type = (
                NewAlertsSourceDataAttributesResolutionRuleAttributesConditionsAttributesItemConditionableType(
                    _conditionable_type
                )
            )

        conditionable_id = d.pop("conditionable_id", UNSET)

        _kind = d.pop("kind", UNSET)
        kind: Union[Unset, NewAlertsSourceDataAttributesResolutionRuleAttributesConditionsAttributesItemKind]
        if isinstance(_kind, Unset):
            kind = UNSET
        else:
            kind = NewAlertsSourceDataAttributesResolutionRuleAttributesConditionsAttributesItemKind(_kind)

        new_alerts_source_data_attributes_resolution_rule_attributes_conditions_attributes_item = cls(
            field=field,
            operator=operator,
            value=value,
            conditionable_type=conditionable_type,
            conditionable_id=conditionable_id,
            kind=kind,
        )

        new_alerts_source_data_attributes_resolution_rule_attributes_conditions_attributes_item.additional_properties = d
        return new_alerts_source_data_attributes_resolution_rule_attributes_conditions_attributes_item

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
