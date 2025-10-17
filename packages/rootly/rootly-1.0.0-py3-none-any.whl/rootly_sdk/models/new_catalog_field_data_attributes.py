from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define

from ..models.new_catalog_field_data_attributes_kind import NewCatalogFieldDataAttributesKind
from ..types import UNSET, Unset

T = TypeVar("T", bound="NewCatalogFieldDataAttributes")


@_attrs_define
class NewCatalogFieldDataAttributes:
    """
    Attributes:
        name (str):
        kind (NewCatalogFieldDataAttributesKind):
        kind_catalog_id (Union[None, Unset, str]): Restricts values to items of specified catalog.
        multiple (Union[Unset, bool]): Whether the attribute accepts multiple values.
        position (Union[None, Unset, int]): Default position of the item when displayed in a list.
    """

    name: str
    kind: NewCatalogFieldDataAttributesKind
    kind_catalog_id: Union[None, Unset, str] = UNSET
    multiple: Union[Unset, bool] = UNSET
    position: Union[None, Unset, int] = UNSET

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        kind = self.kind.value

        kind_catalog_id: Union[None, Unset, str]
        if isinstance(self.kind_catalog_id, Unset):
            kind_catalog_id = UNSET
        else:
            kind_catalog_id = self.kind_catalog_id

        multiple = self.multiple

        position: Union[None, Unset, int]
        if isinstance(self.position, Unset):
            position = UNSET
        else:
            position = self.position

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "name": name,
                "kind": kind,
            }
        )
        if kind_catalog_id is not UNSET:
            field_dict["kind_catalog_id"] = kind_catalog_id
        if multiple is not UNSET:
            field_dict["multiple"] = multiple
        if position is not UNSET:
            field_dict["position"] = position

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        name = d.pop("name")

        kind = NewCatalogFieldDataAttributesKind(d.pop("kind"))

        def _parse_kind_catalog_id(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        kind_catalog_id = _parse_kind_catalog_id(d.pop("kind_catalog_id", UNSET))

        multiple = d.pop("multiple", UNSET)

        def _parse_position(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        position = _parse_position(d.pop("position", UNSET))

        new_catalog_field_data_attributes = cls(
            name=name,
            kind=kind,
            kind_catalog_id=kind_catalog_id,
            multiple=multiple,
            position=position,
        )

        return new_catalog_field_data_attributes
