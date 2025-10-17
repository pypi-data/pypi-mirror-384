from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.dashboard_panel_params_datasets_item_collection import DashboardPanelParamsDatasetsItemCollection
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.dashboard_panel_params_datasets_item_aggregate_type_0 import (
        DashboardPanelParamsDatasetsItemAggregateType0,
    )
    from ..models.dashboard_panel_params_datasets_item_filter_item import DashboardPanelParamsDatasetsItemFilterItem


T = TypeVar("T", bound="DashboardPanelParamsDatasetsItem")


@_attrs_define
class DashboardPanelParamsDatasetsItem:
    """
    Attributes:
        name (Union[None, Unset, str]):
        collection (Union[Unset, DashboardPanelParamsDatasetsItemCollection]):
        filter_ (Union[Unset, list['DashboardPanelParamsDatasetsItemFilterItem']]):
        group_by (Union[None, Unset, str]):
        aggregate (Union['DashboardPanelParamsDatasetsItemAggregateType0', None, Unset]):
    """

    name: Union[None, Unset, str] = UNSET
    collection: Union[Unset, DashboardPanelParamsDatasetsItemCollection] = UNSET
    filter_: Union[Unset, list["DashboardPanelParamsDatasetsItemFilterItem"]] = UNSET
    group_by: Union[None, Unset, str] = UNSET
    aggregate: Union["DashboardPanelParamsDatasetsItemAggregateType0", None, Unset] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.dashboard_panel_params_datasets_item_aggregate_type_0 import (
            DashboardPanelParamsDatasetsItemAggregateType0,
        )

        name: Union[None, Unset, str]
        if isinstance(self.name, Unset):
            name = UNSET
        else:
            name = self.name

        collection: Union[Unset, str] = UNSET
        if not isinstance(self.collection, Unset):
            collection = self.collection.value

        filter_: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.filter_, Unset):
            filter_ = []
            for filter_item_data in self.filter_:
                filter_item = filter_item_data.to_dict()
                filter_.append(filter_item)

        group_by: Union[None, Unset, str]
        if isinstance(self.group_by, Unset):
            group_by = UNSET
        else:
            group_by = self.group_by

        aggregate: Union[None, Unset, dict[str, Any]]
        if isinstance(self.aggregate, Unset):
            aggregate = UNSET
        elif isinstance(self.aggregate, DashboardPanelParamsDatasetsItemAggregateType0):
            aggregate = self.aggregate.to_dict()
        else:
            aggregate = self.aggregate

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if name is not UNSET:
            field_dict["name"] = name
        if collection is not UNSET:
            field_dict["collection"] = collection
        if filter_ is not UNSET:
            field_dict["filter"] = filter_
        if group_by is not UNSET:
            field_dict["group_by"] = group_by
        if aggregate is not UNSET:
            field_dict["aggregate"] = aggregate

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        from ..models.dashboard_panel_params_datasets_item_aggregate_type_0 import (
            DashboardPanelParamsDatasetsItemAggregateType0,
        )
        from ..models.dashboard_panel_params_datasets_item_filter_item import DashboardPanelParamsDatasetsItemFilterItem

        d = src_dict.copy()

        def _parse_name(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        name = _parse_name(d.pop("name", UNSET))

        _collection = d.pop("collection", UNSET)
        collection: Union[Unset, DashboardPanelParamsDatasetsItemCollection]
        if isinstance(_collection, Unset):
            collection = UNSET
        else:
            collection = DashboardPanelParamsDatasetsItemCollection(_collection)

        filter_ = []
        _filter_ = d.pop("filter", UNSET)
        for filter_item_data in _filter_ or []:
            filter_item = DashboardPanelParamsDatasetsItemFilterItem.from_dict(filter_item_data)

            filter_.append(filter_item)

        def _parse_group_by(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        group_by = _parse_group_by(d.pop("group_by", UNSET))

        def _parse_aggregate(data: object) -> Union["DashboardPanelParamsDatasetsItemAggregateType0", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                aggregate_type_0 = DashboardPanelParamsDatasetsItemAggregateType0.from_dict(data)

                return aggregate_type_0
            except:  # noqa: E722
                pass
            return cast(Union["DashboardPanelParamsDatasetsItemAggregateType0", None, Unset], data)

        aggregate = _parse_aggregate(d.pop("aggregate", UNSET))

        dashboard_panel_params_datasets_item = cls(
            name=name,
            collection=collection,
            filter_=filter_,
            group_by=group_by,
            aggregate=aggregate,
        )

        dashboard_panel_params_datasets_item.additional_properties = d
        return dashboard_panel_params_datasets_item

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
