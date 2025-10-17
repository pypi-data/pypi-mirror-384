from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.dashboard_panel_params_datasets_item_aggregate_type_0_operation import (
    DashboardPanelParamsDatasetsItemAggregateType0Operation,
)
from ..types import UNSET, Unset

T = TypeVar("T", bound="DashboardPanelParamsDatasetsItemAggregateType0")


@_attrs_define
class DashboardPanelParamsDatasetsItemAggregateType0:
    """
    Attributes:
        operation (Union[Unset, DashboardPanelParamsDatasetsItemAggregateType0Operation]):
        key (Union[None, Unset, str]):
        cumulative (Union[None, Unset, bool]):
    """

    operation: Union[Unset, DashboardPanelParamsDatasetsItemAggregateType0Operation] = UNSET
    key: Union[None, Unset, str] = UNSET
    cumulative: Union[None, Unset, bool] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        operation: Union[Unset, str] = UNSET
        if not isinstance(self.operation, Unset):
            operation = self.operation.value

        key: Union[None, Unset, str]
        if isinstance(self.key, Unset):
            key = UNSET
        else:
            key = self.key

        cumulative: Union[None, Unset, bool]
        if isinstance(self.cumulative, Unset):
            cumulative = UNSET
        else:
            cumulative = self.cumulative

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if operation is not UNSET:
            field_dict["operation"] = operation
        if key is not UNSET:
            field_dict["key"] = key
        if cumulative is not UNSET:
            field_dict["cumulative"] = cumulative

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        _operation = d.pop("operation", UNSET)
        operation: Union[Unset, DashboardPanelParamsDatasetsItemAggregateType0Operation]
        if isinstance(_operation, Unset):
            operation = UNSET
        else:
            operation = DashboardPanelParamsDatasetsItemAggregateType0Operation(_operation)

        def _parse_key(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        key = _parse_key(d.pop("key", UNSET))

        def _parse_cumulative(data: object) -> Union[None, Unset, bool]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, bool], data)

        cumulative = _parse_cumulative(d.pop("cumulative", UNSET))

        dashboard_panel_params_datasets_item_aggregate_type_0 = cls(
            operation=operation,
            key=key,
            cumulative=cumulative,
        )

        dashboard_panel_params_datasets_item_aggregate_type_0.additional_properties = d
        return dashboard_panel_params_datasets_item_aggregate_type_0

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
