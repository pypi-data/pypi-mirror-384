from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.schedule_rotation_user_list_data_item_type import (
    ScheduleRotationUserListDataItemType,
    check_schedule_rotation_user_list_data_item_type,
)

if TYPE_CHECKING:
    from ..models.schedule_rotation_user import ScheduleRotationUser


T = TypeVar("T", bound="ScheduleRotationUserListDataItem")


@_attrs_define
class ScheduleRotationUserListDataItem:
    """
    Attributes:
        id (str): Unique ID of the schedule rotation user
        type_ (ScheduleRotationUserListDataItemType):
        attributes (ScheduleRotationUser):
    """

    id: str
    type_: ScheduleRotationUserListDataItemType
    attributes: "ScheduleRotationUser"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        type_: str = self.type_

        attributes = self.attributes.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "type": type_,
                "attributes": attributes,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.schedule_rotation_user import ScheduleRotationUser

        d = dict(src_dict)
        id = d.pop("id")

        type_ = check_schedule_rotation_user_list_data_item_type(d.pop("type"))

        attributes = ScheduleRotationUser.from_dict(d.pop("attributes"))

        schedule_rotation_user_list_data_item = cls(
            id=id,
            type_=type_,
            attributes=attributes,
        )

        schedule_rotation_user_list_data_item.additional_properties = d
        return schedule_rotation_user_list_data_item

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
