from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.escalation_policy_path_rules_item_type_2_operator import EscalationPolicyPathRulesItemType2Operator
from ..models.escalation_policy_path_rules_item_type_2_rule_type import EscalationPolicyPathRulesItemType2RuleType

T = TypeVar("T", bound="EscalationPolicyPathRulesItemType2")


@_attrs_define
class EscalationPolicyPathRulesItemType2:
    """
    Attributes:
        rule_type (EscalationPolicyPathRulesItemType2RuleType): The type of the escalation path rule
        json_path (str): JSON path to extract value from payload
        operator (EscalationPolicyPathRulesItemType2Operator): How JSON path value should be matched
        value (str): Value with which JSON path value should be matched
    """

    rule_type: EscalationPolicyPathRulesItemType2RuleType
    json_path: str
    operator: EscalationPolicyPathRulesItemType2Operator
    value: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        rule_type = self.rule_type.value

        json_path = self.json_path

        operator = self.operator.value

        value = self.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "rule_type": rule_type,
                "json_path": json_path,
                "operator": operator,
                "value": value,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        rule_type = EscalationPolicyPathRulesItemType2RuleType(d.pop("rule_type"))

        json_path = d.pop("json_path")

        operator = EscalationPolicyPathRulesItemType2Operator(d.pop("operator"))

        value = d.pop("value")

        escalation_policy_path_rules_item_type_2 = cls(
            rule_type=rule_type,
            json_path=json_path,
            operator=operator,
            value=value,
        )

        escalation_policy_path_rules_item_type_2.additional_properties = d
        return escalation_policy_path_rules_item_type_2

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
