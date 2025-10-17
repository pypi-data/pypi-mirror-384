from typing import Any, TypeVar, Union

from attrs import define as _attrs_define

from ..models.update_catalog_entity_property_data_attributes_key import UpdateCatalogEntityPropertyDataAttributesKey
from ..types import UNSET, Unset

T = TypeVar("T", bound="UpdateCatalogEntityPropertyDataAttributes")


@_attrs_define
class UpdateCatalogEntityPropertyDataAttributes:
    """
    Attributes:
        key (Union[Unset, UpdateCatalogEntityPropertyDataAttributesKey]):
        value (Union[Unset, str]):
    """

    key: Union[Unset, UpdateCatalogEntityPropertyDataAttributesKey] = UNSET
    value: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        key: Union[Unset, str] = UNSET
        if not isinstance(self.key, Unset):
            key = self.key.value

        value = self.value

        field_dict: dict[str, Any] = {}
        field_dict.update({})
        if key is not UNSET:
            field_dict["key"] = key
        if value is not UNSET:
            field_dict["value"] = value

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        _key = d.pop("key", UNSET)
        key: Union[Unset, UpdateCatalogEntityPropertyDataAttributesKey]
        if isinstance(_key, Unset):
            key = UNSET
        else:
            key = UpdateCatalogEntityPropertyDataAttributesKey(_key)

        value = d.pop("value", UNSET)

        update_catalog_entity_property_data_attributes = cls(
            key=key,
            value=value,
        )

        return update_catalog_entity_property_data_attributes
