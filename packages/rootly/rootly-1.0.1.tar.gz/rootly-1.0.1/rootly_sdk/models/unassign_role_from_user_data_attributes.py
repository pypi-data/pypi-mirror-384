from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="UnassignRoleFromUserDataAttributes")


@_attrs_define
class UnassignRoleFromUserDataAttributes:
    """
    Attributes:
        user_id (Union[Unset, str]): ID of user you wish to remove as assigned user from this incident
        incident_role_id (Union[Unset, str]): ID of the incident role
    """

    user_id: Union[Unset, str] = UNSET
    incident_role_id: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        user_id = self.user_id

        incident_role_id = self.incident_role_id

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if user_id is not UNSET:
            field_dict["user_id"] = user_id
        if incident_role_id is not UNSET:
            field_dict["incident_role_id"] = incident_role_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        user_id = d.pop("user_id", UNSET)

        incident_role_id = d.pop("incident_role_id", UNSET)

        unassign_role_from_user_data_attributes = cls(
            user_id=user_id,
            incident_role_id=incident_role_id,
        )

        return unassign_role_from_user_data_attributes
