from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.alert_routing_rule_response_data import AlertRoutingRuleResponseData


T = TypeVar("T", bound="AlertRoutingRuleResponse")


@_attrs_define
class AlertRoutingRuleResponse:
    """
    Attributes:
        data (AlertRoutingRuleResponseData):
    """

    data: "AlertRoutingRuleResponseData"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = self.data.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "data": data,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        from ..models.alert_routing_rule_response_data import AlertRoutingRuleResponseData

        d = src_dict.copy()
        data = AlertRoutingRuleResponseData.from_dict(d.pop("data"))

        alert_routing_rule_response = cls(
            data=data,
        )

        alert_routing_rule_response.additional_properties = d
        return alert_routing_rule_response

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
