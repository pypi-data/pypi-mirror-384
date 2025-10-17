from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define

from ..models.new_incident_permission_set_data_attributes_private_incident_permissions_item import (
    NewIncidentPermissionSetDataAttributesPrivateIncidentPermissionsItem,
)
from ..models.new_incident_permission_set_data_attributes_public_incident_permissions_item import (
    NewIncidentPermissionSetDataAttributesPublicIncidentPermissionsItem,
)
from ..types import UNSET, Unset

T = TypeVar("T", bound="NewIncidentPermissionSetDataAttributes")


@_attrs_define
class NewIncidentPermissionSetDataAttributes:
    """
    Attributes:
        name (str): The incident permission set name.
        slug (Union[Unset, str]): The incident permission set slug.
        description (Union[None, Unset, str]): The incident permission set description.
        private_incident_permissions (Union[Unset,
            list[NewIncidentPermissionSetDataAttributesPrivateIncidentPermissionsItem]]):
        public_incident_permissions (Union[Unset,
            list[NewIncidentPermissionSetDataAttributesPublicIncidentPermissionsItem]]):
    """

    name: str
    slug: Union[Unset, str] = UNSET
    description: Union[None, Unset, str] = UNSET
    private_incident_permissions: Union[
        Unset, list[NewIncidentPermissionSetDataAttributesPrivateIncidentPermissionsItem]
    ] = UNSET
    public_incident_permissions: Union[
        Unset, list[NewIncidentPermissionSetDataAttributesPublicIncidentPermissionsItem]
    ] = UNSET

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        slug = self.slug

        description: Union[None, Unset, str]
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        private_incident_permissions: Union[Unset, list[str]] = UNSET
        if not isinstance(self.private_incident_permissions, Unset):
            private_incident_permissions = []
            for private_incident_permissions_item_data in self.private_incident_permissions:
                private_incident_permissions_item = private_incident_permissions_item_data.value
                private_incident_permissions.append(private_incident_permissions_item)

        public_incident_permissions: Union[Unset, list[str]] = UNSET
        if not isinstance(self.public_incident_permissions, Unset):
            public_incident_permissions = []
            for public_incident_permissions_item_data in self.public_incident_permissions:
                public_incident_permissions_item = public_incident_permissions_item_data.value
                public_incident_permissions.append(public_incident_permissions_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "name": name,
            }
        )
        if slug is not UNSET:
            field_dict["slug"] = slug
        if description is not UNSET:
            field_dict["description"] = description
        if private_incident_permissions is not UNSET:
            field_dict["private_incident_permissions"] = private_incident_permissions
        if public_incident_permissions is not UNSET:
            field_dict["public_incident_permissions"] = public_incident_permissions

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        name = d.pop("name")

        slug = d.pop("slug", UNSET)

        def _parse_description(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        description = _parse_description(d.pop("description", UNSET))

        private_incident_permissions = []
        _private_incident_permissions = d.pop("private_incident_permissions", UNSET)
        for private_incident_permissions_item_data in _private_incident_permissions or []:
            private_incident_permissions_item = NewIncidentPermissionSetDataAttributesPrivateIncidentPermissionsItem(
                private_incident_permissions_item_data
            )

            private_incident_permissions.append(private_incident_permissions_item)

        public_incident_permissions = []
        _public_incident_permissions = d.pop("public_incident_permissions", UNSET)
        for public_incident_permissions_item_data in _public_incident_permissions or []:
            public_incident_permissions_item = NewIncidentPermissionSetDataAttributesPublicIncidentPermissionsItem(
                public_incident_permissions_item_data
            )

            public_incident_permissions.append(public_incident_permissions_item)

        new_incident_permission_set_data_attributes = cls(
            name=name,
            slug=slug,
            description=description,
            private_incident_permissions=private_incident_permissions,
            public_incident_permissions=public_incident_permissions,
        )

        return new_incident_permission_set_data_attributes
