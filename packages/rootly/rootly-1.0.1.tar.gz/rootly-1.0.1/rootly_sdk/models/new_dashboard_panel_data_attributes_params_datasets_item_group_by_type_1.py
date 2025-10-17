from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.new_dashboard_panel_data_attributes_params_datasets_item_group_by_type_1_key import (
    NewDashboardPanelDataAttributesParamsDatasetsItemGroupByType1Key,
    check_new_dashboard_panel_data_attributes_params_datasets_item_group_by_type_1_key,
)

T = TypeVar("T", bound="NewDashboardPanelDataAttributesParamsDatasetsItemGroupByType1")


@_attrs_define
class NewDashboardPanelDataAttributesParamsDatasetsItemGroupByType1:
    """
    Attributes:
        key (NewDashboardPanelDataAttributesParamsDatasetsItemGroupByType1Key):
        value (str):
    """

    key: NewDashboardPanelDataAttributesParamsDatasetsItemGroupByType1Key
    value: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        key: str = self.key

        value = self.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "key": key,
                "value": value,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        key = check_new_dashboard_panel_data_attributes_params_datasets_item_group_by_type_1_key(d.pop("key"))

        value = d.pop("value")

        new_dashboard_panel_data_attributes_params_datasets_item_group_by_type_1 = cls(
            key=key,
            value=value,
        )

        new_dashboard_panel_data_attributes_params_datasets_item_group_by_type_1.additional_properties = d
        return new_dashboard_panel_data_attributes_params_datasets_item_group_by_type_1

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
