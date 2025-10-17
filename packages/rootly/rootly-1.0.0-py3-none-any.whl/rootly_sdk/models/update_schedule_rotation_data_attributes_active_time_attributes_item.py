from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="UpdateScheduleRotationDataAttributesActiveTimeAttributesItem")


@_attrs_define
class UpdateScheduleRotationDataAttributesActiveTimeAttributesItem:
    """
    Attributes:
        start_time (str): Start time for schedule rotation active time
        end_time (str): End time for schedule rotation active time
    """

    start_time: str
    end_time: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        start_time = self.start_time

        end_time = self.end_time

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "start_time": start_time,
                "end_time": end_time,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        start_time = d.pop("start_time")

        end_time = d.pop("end_time")

        update_schedule_rotation_data_attributes_active_time_attributes_item = cls(
            start_time=start_time,
            end_time=end_time,
        )

        update_schedule_rotation_data_attributes_active_time_attributes_item.additional_properties = d
        return update_schedule_rotation_data_attributes_active_time_attributes_item

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
