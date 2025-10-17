from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.dashboard_panel_params_legend_groups import DashboardPanelParamsLegendGroups
from ..types import UNSET, Unset

T = TypeVar("T", bound="DashboardPanelParamsLegend")


@_attrs_define
class DashboardPanelParamsLegend:
    """
    Attributes:
        groups (Union[Unset, DashboardPanelParamsLegendGroups]):  Default: DashboardPanelParamsLegendGroups.ALL.
    """

    groups: Union[Unset, DashboardPanelParamsLegendGroups] = DashboardPanelParamsLegendGroups.ALL
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        groups: Union[Unset, str] = UNSET
        if not isinstance(self.groups, Unset):
            groups = self.groups.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if groups is not UNSET:
            field_dict["groups"] = groups

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        _groups = d.pop("groups", UNSET)
        groups: Union[Unset, DashboardPanelParamsLegendGroups]
        if isinstance(_groups, Unset):
            groups = UNSET
        else:
            groups = DashboardPanelParamsLegendGroups(_groups)

        dashboard_panel_params_legend = cls(
            groups=groups,
        )

        dashboard_panel_params_legend.additional_properties = d
        return dashboard_panel_params_legend

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
