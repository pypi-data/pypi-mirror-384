from typing import TYPE_CHECKING, Any, TypeVar, Union, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.alert_routing_rule_condition_type import AlertRoutingRuleConditionType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.alert_routing_rule_conditions_item import AlertRoutingRuleConditionsItem
    from ..models.alert_routing_rule_destination_type_0 import AlertRoutingRuleDestinationType0


T = TypeVar("T", bound="AlertRoutingRule")


@_attrs_define
class AlertRoutingRule:
    """
    Attributes:
        name (str): The name of the alert routing rule
        enabled (bool): Whether the alert routing rule is enabled
        alerts_source_id (UUID): The ID of the alerts source
        position (int): The position of the alert routing rule for ordering evaluation
        condition_type (AlertRoutingRuleConditionType): The type of condition for the alert routing rule
        created_at (str): Date of creation
        updated_at (str): Date of last update
        conditions (Union[Unset, list['AlertRoutingRuleConditionsItem']]): The conditions for the alert routing rule
        destination (Union['AlertRoutingRuleDestinationType0', None, Unset]): The destinations for the alert routing
            rule
    """

    name: str
    enabled: bool
    alerts_source_id: UUID
    position: int
    condition_type: AlertRoutingRuleConditionType
    created_at: str
    updated_at: str
    conditions: Union[Unset, list["AlertRoutingRuleConditionsItem"]] = UNSET
    destination: Union["AlertRoutingRuleDestinationType0", None, Unset] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.alert_routing_rule_destination_type_0 import AlertRoutingRuleDestinationType0

        name = self.name

        enabled = self.enabled

        alerts_source_id = str(self.alerts_source_id)

        position = self.position

        condition_type = self.condition_type.value

        created_at = self.created_at

        updated_at = self.updated_at

        conditions: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.conditions, Unset):
            conditions = []
            for conditions_item_data in self.conditions:
                conditions_item = conditions_item_data.to_dict()
                conditions.append(conditions_item)

        destination: Union[None, Unset, dict[str, Any]]
        if isinstance(self.destination, Unset):
            destination = UNSET
        elif isinstance(self.destination, AlertRoutingRuleDestinationType0):
            destination = self.destination.to_dict()
        else:
            destination = self.destination

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "enabled": enabled,
                "alerts_source_id": alerts_source_id,
                "position": position,
                "condition_type": condition_type,
                "created_at": created_at,
                "updated_at": updated_at,
            }
        )
        if conditions is not UNSET:
            field_dict["conditions"] = conditions
        if destination is not UNSET:
            field_dict["destination"] = destination

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        from ..models.alert_routing_rule_conditions_item import AlertRoutingRuleConditionsItem
        from ..models.alert_routing_rule_destination_type_0 import AlertRoutingRuleDestinationType0

        d = src_dict.copy()
        name = d.pop("name")

        enabled = d.pop("enabled")

        alerts_source_id = UUID(d.pop("alerts_source_id"))

        position = d.pop("position")

        condition_type = AlertRoutingRuleConditionType(d.pop("condition_type"))

        created_at = d.pop("created_at")

        updated_at = d.pop("updated_at")

        conditions = []
        _conditions = d.pop("conditions", UNSET)
        for conditions_item_data in _conditions or []:
            conditions_item = AlertRoutingRuleConditionsItem.from_dict(conditions_item_data)

            conditions.append(conditions_item)

        def _parse_destination(data: object) -> Union["AlertRoutingRuleDestinationType0", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                destination_type_0 = AlertRoutingRuleDestinationType0.from_dict(data)

                return destination_type_0
            except:  # noqa: E722
                pass
            return cast(Union["AlertRoutingRuleDestinationType0", None, Unset], data)

        destination = _parse_destination(d.pop("destination", UNSET))

        alert_routing_rule = cls(
            name=name,
            enabled=enabled,
            alerts_source_id=alerts_source_id,
            position=position,
            condition_type=condition_type,
            created_at=created_at,
            updated_at=updated_at,
            conditions=conditions,
            destination=destination,
        )

        alert_routing_rule.additional_properties = d
        return alert_routing_rule

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
