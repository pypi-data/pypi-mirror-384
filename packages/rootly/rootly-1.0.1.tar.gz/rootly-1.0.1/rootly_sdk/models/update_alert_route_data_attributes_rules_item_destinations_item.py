from collections.abc import Mapping
from typing import Any, TypeVar, Union
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.update_alert_route_data_attributes_rules_item_destinations_item_target_type import (
    UpdateAlertRouteDataAttributesRulesItemDestinationsItemTargetType,
    check_update_alert_route_data_attributes_rules_item_destinations_item_target_type,
)
from ..types import UNSET, Unset

T = TypeVar("T", bound="UpdateAlertRouteDataAttributesRulesItemDestinationsItem")


@_attrs_define
class UpdateAlertRouteDataAttributesRulesItemDestinationsItem:
    """
    Attributes:
        target_type (UpdateAlertRouteDataAttributesRulesItemDestinationsItemTargetType): The type of the target
        target_id (UUID): The ID of the target
        id (Union[Unset, UUID]): The ID of the target (for updates)
    """

    target_type: UpdateAlertRouteDataAttributesRulesItemDestinationsItemTargetType
    target_id: UUID
    id: Union[Unset, UUID] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        target_type: str = self.target_type

        target_id = str(self.target_id)

        id: Union[Unset, str] = UNSET
        if not isinstance(self.id, Unset):
            id = str(self.id)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "target_type": target_type,
                "target_id": target_id,
            }
        )
        if id is not UNSET:
            field_dict["id"] = id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        target_type = check_update_alert_route_data_attributes_rules_item_destinations_item_target_type(
            d.pop("target_type")
        )

        target_id = UUID(d.pop("target_id"))

        _id = d.pop("id", UNSET)
        id: Union[Unset, UUID]
        if isinstance(_id, Unset):
            id = UNSET
        else:
            id = UUID(_id)

        update_alert_route_data_attributes_rules_item_destinations_item = cls(
            target_type=target_type,
            target_id=target_id,
            id=id,
        )

        update_alert_route_data_attributes_rules_item_destinations_item.additional_properties = d
        return update_alert_route_data_attributes_rules_item_destinations_item

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
