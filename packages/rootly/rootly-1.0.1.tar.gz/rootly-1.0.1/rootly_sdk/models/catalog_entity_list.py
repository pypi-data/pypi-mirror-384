from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.catalog_entity_list_data_item import CatalogEntityListDataItem
    from ..models.links import Links


T = TypeVar("T", bound="CatalogEntityList")


@_attrs_define
class CatalogEntityList:
    """
    Attributes:
        data (list['CatalogEntityListDataItem']):
        links (Links):
    """

    data: list["CatalogEntityListDataItem"]
    links: "Links"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = []
        for data_item_data in self.data:
            data_item = data_item_data.to_dict()
            data.append(data_item)

        links = self.links.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "data": data,
                "links": links,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.catalog_entity_list_data_item import CatalogEntityListDataItem
        from ..models.links import Links

        d = dict(src_dict)
        data = []
        _data = d.pop("data")
        for data_item_data in _data:
            data_item = CatalogEntityListDataItem.from_dict(data_item_data)

            data.append(data_item)

        links = Links.from_dict(d.pop("links"))

        catalog_entity_list = cls(
            data=data,
            links=links,
        )

        catalog_entity_list.additional_properties = d
        return catalog_entity_list

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
