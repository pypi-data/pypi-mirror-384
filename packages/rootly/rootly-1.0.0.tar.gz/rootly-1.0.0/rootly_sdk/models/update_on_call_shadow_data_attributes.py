import datetime
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from dateutil.parser import isoparse

from ..models.update_on_call_shadow_data_attributes_shadowable_type import (
    UpdateOnCallShadowDataAttributesShadowableType,
)
from ..types import UNSET, Unset

T = TypeVar("T", bound="UpdateOnCallShadowDataAttributes")


@_attrs_define
class UpdateOnCallShadowDataAttributes:
    """
    Attributes:
        schedule_id (Union[Unset, str]): ID of schedule the shadow shift belongs to
        shadowable_type (Union[Unset, UpdateOnCallShadowDataAttributesShadowableType]):
        shadowable_id (Union[Unset, str]): ID of schedule or user the shadow user is shadowing
        shadow_user_id (Union[Unset, int]): Which user the shadow shift belongs to.
        starts_at (Union[Unset, datetime.datetime]): Start datetime of shadow shift
        ends_at (Union[Unset, datetime.datetime]): End datetime for shadow shift
    """

    schedule_id: Union[Unset, str] = UNSET
    shadowable_type: Union[Unset, UpdateOnCallShadowDataAttributesShadowableType] = UNSET
    shadowable_id: Union[Unset, str] = UNSET
    shadow_user_id: Union[Unset, int] = UNSET
    starts_at: Union[Unset, datetime.datetime] = UNSET
    ends_at: Union[Unset, datetime.datetime] = UNSET

    def to_dict(self) -> dict[str, Any]:
        schedule_id = self.schedule_id

        shadowable_type: Union[Unset, str] = UNSET
        if not isinstance(self.shadowable_type, Unset):
            shadowable_type = self.shadowable_type.value

        shadowable_id = self.shadowable_id

        shadow_user_id = self.shadow_user_id

        starts_at: Union[Unset, str] = UNSET
        if not isinstance(self.starts_at, Unset):
            starts_at = self.starts_at.isoformat()

        ends_at: Union[Unset, str] = UNSET
        if not isinstance(self.ends_at, Unset):
            ends_at = self.ends_at.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update({})
        if schedule_id is not UNSET:
            field_dict["schedule_id"] = schedule_id
        if shadowable_type is not UNSET:
            field_dict["shadowable_type"] = shadowable_type
        if shadowable_id is not UNSET:
            field_dict["shadowable_id"] = shadowable_id
        if shadow_user_id is not UNSET:
            field_dict["shadow_user_id"] = shadow_user_id
        if starts_at is not UNSET:
            field_dict["starts_at"] = starts_at
        if ends_at is not UNSET:
            field_dict["ends_at"] = ends_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        schedule_id = d.pop("schedule_id", UNSET)

        _shadowable_type = d.pop("shadowable_type", UNSET)
        shadowable_type: Union[Unset, UpdateOnCallShadowDataAttributesShadowableType]
        if isinstance(_shadowable_type, Unset):
            shadowable_type = UNSET
        else:
            shadowable_type = UpdateOnCallShadowDataAttributesShadowableType(_shadowable_type)

        shadowable_id = d.pop("shadowable_id", UNSET)

        shadow_user_id = d.pop("shadow_user_id", UNSET)

        _starts_at = d.pop("starts_at", UNSET)
        starts_at: Union[Unset, datetime.datetime]
        if isinstance(_starts_at, Unset):
            starts_at = UNSET
        else:
            starts_at = isoparse(_starts_at)

        _ends_at = d.pop("ends_at", UNSET)
        ends_at: Union[Unset, datetime.datetime]
        if isinstance(_ends_at, Unset):
            ends_at = UNSET
        else:
            ends_at = isoparse(_ends_at)

        update_on_call_shadow_data_attributes = cls(
            schedule_id=schedule_id,
            shadowable_type=shadowable_type,
            shadowable_id=shadowable_id,
            shadow_user_id=shadow_user_id,
            starts_at=starts_at,
            ends_at=ends_at,
        )

        return update_on_call_shadow_data_attributes
