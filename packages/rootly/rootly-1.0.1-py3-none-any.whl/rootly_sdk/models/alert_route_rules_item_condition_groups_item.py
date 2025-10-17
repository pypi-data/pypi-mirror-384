from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.alert_route_rules_item_condition_groups_item_conditions_item import (
        AlertRouteRulesItemConditionGroupsItemConditionsItem,
    )


T = TypeVar("T", bound="AlertRouteRulesItemConditionGroupsItem")


@_attrs_define
class AlertRouteRulesItemConditionGroupsItem:
    """
    Attributes:
        conditions (list['AlertRouteRulesItemConditionGroupsItemConditionsItem']):
        position (Union[Unset, int]): The position of the condition group
    """

    conditions: list["AlertRouteRulesItemConditionGroupsItemConditionsItem"]
    position: Union[Unset, int] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        conditions = []
        for conditions_item_data in self.conditions:
            conditions_item = conditions_item_data.to_dict()
            conditions.append(conditions_item)

        position = self.position

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "conditions": conditions,
            }
        )
        if position is not UNSET:
            field_dict["position"] = position

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.alert_route_rules_item_condition_groups_item_conditions_item import (
            AlertRouteRulesItemConditionGroupsItemConditionsItem,
        )

        d = dict(src_dict)
        conditions = []
        _conditions = d.pop("conditions")
        for conditions_item_data in _conditions:
            conditions_item = AlertRouteRulesItemConditionGroupsItemConditionsItem.from_dict(conditions_item_data)

            conditions.append(conditions_item)

        position = d.pop("position", UNSET)

        alert_route_rules_item_condition_groups_item = cls(
            conditions=conditions,
            position=position,
        )

        alert_route_rules_item_condition_groups_item.additional_properties = d
        return alert_route_rules_item_condition_groups_item

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
