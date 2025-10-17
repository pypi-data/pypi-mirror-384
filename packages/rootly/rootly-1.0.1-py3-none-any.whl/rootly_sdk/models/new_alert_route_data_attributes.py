from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.new_alert_route_data_attributes_rules_item import NewAlertRouteDataAttributesRulesItem


T = TypeVar("T", bound="NewAlertRouteDataAttributes")


@_attrs_define
class NewAlertRouteDataAttributes:
    """
    Attributes:
        name (str): The name of the alert route
        alerts_source_ids (list[UUID]):
        enabled (Union[Unset, bool]): Whether the alert route is enabled
        owning_team_ids (Union[Unset, list[UUID]]):
        rules (Union[Unset, list['NewAlertRouteDataAttributesRulesItem']]):
    """

    name: str
    alerts_source_ids: list[UUID]
    enabled: Union[Unset, bool] = UNSET
    owning_team_ids: Union[Unset, list[UUID]] = UNSET
    rules: Union[Unset, list["NewAlertRouteDataAttributesRulesItem"]] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        alerts_source_ids = []
        for alerts_source_ids_item_data in self.alerts_source_ids:
            alerts_source_ids_item = str(alerts_source_ids_item_data)
            alerts_source_ids.append(alerts_source_ids_item)

        enabled = self.enabled

        owning_team_ids: Union[Unset, list[str]] = UNSET
        if not isinstance(self.owning_team_ids, Unset):
            owning_team_ids = []
            for owning_team_ids_item_data in self.owning_team_ids:
                owning_team_ids_item = str(owning_team_ids_item_data)
                owning_team_ids.append(owning_team_ids_item)

        rules: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.rules, Unset):
            rules = []
            for rules_item_data in self.rules:
                rules_item = rules_item_data.to_dict()
                rules.append(rules_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "alerts_source_ids": alerts_source_ids,
            }
        )
        if enabled is not UNSET:
            field_dict["enabled"] = enabled
        if owning_team_ids is not UNSET:
            field_dict["owning_team_ids"] = owning_team_ids
        if rules is not UNSET:
            field_dict["rules"] = rules

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.new_alert_route_data_attributes_rules_item import NewAlertRouteDataAttributesRulesItem

        d = dict(src_dict)
        name = d.pop("name")

        alerts_source_ids = []
        _alerts_source_ids = d.pop("alerts_source_ids")
        for alerts_source_ids_item_data in _alerts_source_ids:
            alerts_source_ids_item = UUID(alerts_source_ids_item_data)

            alerts_source_ids.append(alerts_source_ids_item)

        enabled = d.pop("enabled", UNSET)

        owning_team_ids = []
        _owning_team_ids = d.pop("owning_team_ids", UNSET)
        for owning_team_ids_item_data in _owning_team_ids or []:
            owning_team_ids_item = UUID(owning_team_ids_item_data)

            owning_team_ids.append(owning_team_ids_item)

        rules = []
        _rules = d.pop("rules", UNSET)
        for rules_item_data in _rules or []:
            rules_item = NewAlertRouteDataAttributesRulesItem.from_dict(rules_item_data)

            rules.append(rules_item)

        new_alert_route_data_attributes = cls(
            name=name,
            alerts_source_ids=alerts_source_ids,
            enabled=enabled,
            owning_team_ids=owning_team_ids,
            rules=rules,
        )

        new_alert_route_data_attributes.additional_properties = d
        return new_alert_route_data_attributes

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
