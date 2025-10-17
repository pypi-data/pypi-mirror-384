from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.alert_routing_rule_condition import AlertRoutingRuleCondition


T = TypeVar("T", bound="AlertRoutingRuleConditionGroup")


@_attrs_define
class AlertRoutingRuleConditionGroup:
    """A group of conditions for alert routing rule

    Attributes:
        position (int): The position of the condition group for ordering
        id (Union[Unset, UUID]): Unique ID of the condition group
        conditions (Union[Unset, list['AlertRoutingRuleCondition']]): The conditions within this group
        created_at (Union[Unset, str]): Date of creation
        updated_at (Union[Unset, str]): Date of last update
    """

    position: int
    id: Union[Unset, UUID] = UNSET
    conditions: Union[Unset, list["AlertRoutingRuleCondition"]] = UNSET
    created_at: Union[Unset, str] = UNSET
    updated_at: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        position = self.position

        id: Union[Unset, str] = UNSET
        if not isinstance(self.id, Unset):
            id = str(self.id)

        conditions: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.conditions, Unset):
            conditions = []
            for conditions_item_data in self.conditions:
                conditions_item = conditions_item_data.to_dict()
                conditions.append(conditions_item)

        created_at = self.created_at

        updated_at = self.updated_at

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "position": position,
            }
        )
        if id is not UNSET:
            field_dict["id"] = id
        if conditions is not UNSET:
            field_dict["conditions"] = conditions
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.alert_routing_rule_condition import AlertRoutingRuleCondition

        d = dict(src_dict)
        position = d.pop("position")

        _id = d.pop("id", UNSET)
        id: Union[Unset, UUID]
        if isinstance(_id, Unset):
            id = UNSET
        else:
            id = UUID(_id)

        conditions = []
        _conditions = d.pop("conditions", UNSET)
        for conditions_item_data in _conditions or []:
            conditions_item = AlertRoutingRuleCondition.from_dict(conditions_item_data)

            conditions.append(conditions_item)

        created_at = d.pop("created_at", UNSET)

        updated_at = d.pop("updated_at", UNSET)

        alert_routing_rule_condition_group = cls(
            position=position,
            id=id,
            conditions=conditions,
            created_at=created_at,
            updated_at=updated_at,
        )

        alert_routing_rule_condition_group.additional_properties = d
        return alert_routing_rule_condition_group

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
