from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define

from ..models.update_catalog_field_data_attributes_kind import (
    UpdateCatalogFieldDataAttributesKind,
    check_update_catalog_field_data_attributes_kind,
)
from ..types import UNSET, Unset

T = TypeVar("T", bound="UpdateCatalogFieldDataAttributes")


@_attrs_define
class UpdateCatalogFieldDataAttributes:
    """
    Attributes:
        name (Union[Unset, str]):
        slug (Union[Unset, str]):
        kind (Union[Unset, UpdateCatalogFieldDataAttributesKind]):
        kind_catalog_id (Union[None, Unset, str]): Restricts values to items of specified catalog.
        position (Union[None, Unset, int]): Default position of the item when displayed in a list.
    """

    name: Union[Unset, str] = UNSET
    slug: Union[Unset, str] = UNSET
    kind: Union[Unset, UpdateCatalogFieldDataAttributesKind] = UNSET
    kind_catalog_id: Union[None, Unset, str] = UNSET
    position: Union[None, Unset, int] = UNSET

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        slug = self.slug

        kind: Union[Unset, str] = UNSET
        if not isinstance(self.kind, Unset):
            kind = self.kind

        kind_catalog_id: Union[None, Unset, str]
        if isinstance(self.kind_catalog_id, Unset):
            kind_catalog_id = UNSET
        else:
            kind_catalog_id = self.kind_catalog_id

        position: Union[None, Unset, int]
        if isinstance(self.position, Unset):
            position = UNSET
        else:
            position = self.position

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if name is not UNSET:
            field_dict["name"] = name
        if slug is not UNSET:
            field_dict["slug"] = slug
        if kind is not UNSET:
            field_dict["kind"] = kind
        if kind_catalog_id is not UNSET:
            field_dict["kind_catalog_id"] = kind_catalog_id
        if position is not UNSET:
            field_dict["position"] = position

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name", UNSET)

        slug = d.pop("slug", UNSET)

        _kind = d.pop("kind", UNSET)
        kind: Union[Unset, UpdateCatalogFieldDataAttributesKind]
        if isinstance(_kind, Unset):
            kind = UNSET
        else:
            kind = check_update_catalog_field_data_attributes_kind(_kind)

        def _parse_kind_catalog_id(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        kind_catalog_id = _parse_kind_catalog_id(d.pop("kind_catalog_id", UNSET))

        def _parse_position(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        position = _parse_position(d.pop("position", UNSET))

        update_catalog_field_data_attributes = cls(
            name=name,
            slug=slug,
            kind=kind,
            kind_catalog_id=kind_catalog_id,
            position=position,
        )

        return update_catalog_field_data_attributes
