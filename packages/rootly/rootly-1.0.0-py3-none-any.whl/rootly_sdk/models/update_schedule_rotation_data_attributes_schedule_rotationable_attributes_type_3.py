from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..models.update_schedule_rotation_data_attributes_schedule_rotationable_attributes_type_3_shift_length_unit import (
    UpdateScheduleRotationDataAttributesScheduleRotationableAttributesType3ShiftLengthUnit,
)

T = TypeVar("T", bound="UpdateScheduleRotationDataAttributesScheduleRotationableAttributesType3")


@_attrs_define
class UpdateScheduleRotationDataAttributesScheduleRotationableAttributesType3:
    """
    Attributes:
        shift_length (int): Shift length for custom rotation
        shift_length_unit (UpdateScheduleRotationDataAttributesScheduleRotationableAttributesType3ShiftLengthUnit):
            Shift length unit for custom rotation
        handoff_time (str): Hand off time for custom rotation. Use minutes for hourly rotation.
    """

    shift_length: int
    shift_length_unit: UpdateScheduleRotationDataAttributesScheduleRotationableAttributesType3ShiftLengthUnit
    handoff_time: str

    def to_dict(self) -> dict[str, Any]:
        shift_length = self.shift_length

        shift_length_unit = self.shift_length_unit.value

        handoff_time = self.handoff_time

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "shift_length": shift_length,
                "shift_length_unit": shift_length_unit,
                "handoff_time": handoff_time,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        shift_length = d.pop("shift_length")

        shift_length_unit = UpdateScheduleRotationDataAttributesScheduleRotationableAttributesType3ShiftLengthUnit(
            d.pop("shift_length_unit")
        )

        handoff_time = d.pop("handoff_time")

        update_schedule_rotation_data_attributes_schedule_rotationable_attributes_type_3 = cls(
            shift_length=shift_length,
            shift_length_unit=shift_length_unit,
            handoff_time=handoff_time,
        )

        return update_schedule_rotation_data_attributes_schedule_rotationable_attributes_type_3
