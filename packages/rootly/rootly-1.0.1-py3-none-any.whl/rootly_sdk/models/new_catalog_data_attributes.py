from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define

from ..models.new_catalog_data_attributes_icon import (
    NewCatalogDataAttributesIcon,
    check_new_catalog_data_attributes_icon,
)
from ..types import UNSET, Unset

T = TypeVar("T", bound="NewCatalogDataAttributes")


@_attrs_define
class NewCatalogDataAttributes:
    """
    Attributes:
        name (str):
        description (Union[None, Unset, str]):
        icon (Union[Unset, NewCatalogDataAttributesIcon]):
        position (Union[None, Unset, int]): Default position of the catalog when displayed in a list.
    """

    name: str
    description: Union[None, Unset, str] = UNSET
    icon: Union[Unset, NewCatalogDataAttributesIcon] = UNSET
    position: Union[None, Unset, int] = UNSET

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        description: Union[None, Unset, str]
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        icon: Union[Unset, str] = UNSET
        if not isinstance(self.icon, Unset):
            icon = self.icon

        position: Union[None, Unset, int]
        if isinstance(self.position, Unset):
            position = UNSET
        else:
            position = self.position

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "name": name,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description
        if icon is not UNSET:
            field_dict["icon"] = icon
        if position is not UNSET:
            field_dict["position"] = position

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        def _parse_description(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        description = _parse_description(d.pop("description", UNSET))

        _icon = d.pop("icon", UNSET)
        icon: Union[Unset, NewCatalogDataAttributesIcon]
        if isinstance(_icon, Unset):
            icon = UNSET
        else:
            icon = check_new_catalog_data_attributes_icon(_icon)

        def _parse_position(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        position = _parse_position(d.pop("position", UNSET))

        new_catalog_data_attributes = cls(
            name=name,
            description=description,
            icon=icon,
            position=position,
        )

        return new_catalog_data_attributes
