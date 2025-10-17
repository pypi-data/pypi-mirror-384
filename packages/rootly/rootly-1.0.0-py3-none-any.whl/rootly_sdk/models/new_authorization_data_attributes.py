from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..models.new_authorization_data_attributes_authorizable_type import NewAuthorizationDataAttributesAuthorizableType
from ..models.new_authorization_data_attributes_grantee_type import NewAuthorizationDataAttributesGranteeType
from ..models.new_authorization_data_attributes_permissions_item import NewAuthorizationDataAttributesPermissionsItem

T = TypeVar("T", bound="NewAuthorizationDataAttributes")


@_attrs_define
class NewAuthorizationDataAttributes:
    """
    Attributes:
        authorizable_id (str): The id of the resource being accessed.
        authorizable_type (NewAuthorizationDataAttributesAuthorizableType): The type of resource being accessed.
        grantee_id (str): The resource id granted access.
        grantee_type (NewAuthorizationDataAttributesGranteeType): The type of resource granted access.
        permissions (list[NewAuthorizationDataAttributesPermissionsItem]):
    """

    authorizable_id: str
    authorizable_type: NewAuthorizationDataAttributesAuthorizableType
    grantee_id: str
    grantee_type: NewAuthorizationDataAttributesGranteeType
    permissions: list[NewAuthorizationDataAttributesPermissionsItem]

    def to_dict(self) -> dict[str, Any]:
        authorizable_id = self.authorizable_id

        authorizable_type = self.authorizable_type.value

        grantee_id = self.grantee_id

        grantee_type = self.grantee_type.value

        permissions = []
        for permissions_item_data in self.permissions:
            permissions_item = permissions_item_data.value
            permissions.append(permissions_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "authorizable_id": authorizable_id,
                "authorizable_type": authorizable_type,
                "grantee_id": grantee_id,
                "grantee_type": grantee_type,
                "permissions": permissions,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        authorizable_id = d.pop("authorizable_id")

        authorizable_type = NewAuthorizationDataAttributesAuthorizableType(d.pop("authorizable_type"))

        grantee_id = d.pop("grantee_id")

        grantee_type = NewAuthorizationDataAttributesGranteeType(d.pop("grantee_type"))

        permissions = []
        _permissions = d.pop("permissions")
        for permissions_item_data in _permissions:
            permissions_item = NewAuthorizationDataAttributesPermissionsItem(permissions_item_data)

            permissions.append(permissions_item)

        new_authorization_data_attributes = cls(
            authorizable_id=authorizable_id,
            authorizable_type=authorizable_type,
            grantee_id=grantee_id,
            grantee_type=grantee_type,
            permissions=permissions,
        )

        return new_authorization_data_attributes
