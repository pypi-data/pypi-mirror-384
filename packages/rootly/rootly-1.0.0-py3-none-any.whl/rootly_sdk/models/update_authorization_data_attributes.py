from typing import Any, TypeVar, Union

from attrs import define as _attrs_define

from ..models.update_authorization_data_attributes_permissions_item import (
    UpdateAuthorizationDataAttributesPermissionsItem,
)
from ..types import UNSET, Unset

T = TypeVar("T", bound="UpdateAuthorizationDataAttributes")


@_attrs_define
class UpdateAuthorizationDataAttributes:
    """
    Attributes:
        permissions (Union[Unset, list[UpdateAuthorizationDataAttributesPermissionsItem]]):
    """

    permissions: Union[Unset, list[UpdateAuthorizationDataAttributesPermissionsItem]] = UNSET

    def to_dict(self) -> dict[str, Any]:
        permissions: Union[Unset, list[str]] = UNSET
        if not isinstance(self.permissions, Unset):
            permissions = []
            for permissions_item_data in self.permissions:
                permissions_item = permissions_item_data.value
                permissions.append(permissions_item)

        field_dict: dict[str, Any] = {}
        field_dict.update({})
        if permissions is not UNSET:
            field_dict["permissions"] = permissions

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        permissions = []
        _permissions = d.pop("permissions", UNSET)
        for permissions_item_data in _permissions or []:
            permissions_item = UpdateAuthorizationDataAttributesPermissionsItem(permissions_item_data)

            permissions.append(permissions_item)

        update_authorization_data_attributes = cls(
            permissions=permissions,
        )

        return update_authorization_data_attributes
