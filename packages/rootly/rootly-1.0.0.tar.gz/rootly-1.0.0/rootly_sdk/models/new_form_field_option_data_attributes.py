from typing import Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="NewFormFieldOptionDataAttributes")


@_attrs_define
class NewFormFieldOptionDataAttributes:
    """
    Attributes:
        form_field_id (str): The ID of the form field
        value (str): The value of the form_field_option
        color (Union[Unset, str]): The hex color of the form_field_option
        default (Union[Unset, bool]):
        position (Union[Unset, int]): The position of the form_field_option
    """

    form_field_id: str
    value: str
    color: Union[Unset, str] = UNSET
    default: Union[Unset, bool] = UNSET
    position: Union[Unset, int] = UNSET

    def to_dict(self) -> dict[str, Any]:
        form_field_id = self.form_field_id

        value = self.value

        color = self.color

        default = self.default

        position = self.position

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "form_field_id": form_field_id,
                "value": value,
            }
        )
        if color is not UNSET:
            field_dict["color"] = color
        if default is not UNSET:
            field_dict["default"] = default
        if position is not UNSET:
            field_dict["position"] = position

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        form_field_id = d.pop("form_field_id")

        value = d.pop("value")

        color = d.pop("color", UNSET)

        default = d.pop("default", UNSET)

        position = d.pop("position", UNSET)

        new_form_field_option_data_attributes = cls(
            form_field_id=form_field_id,
            value=value,
            color=color,
            default=default,
            position=position,
        )

        return new_form_field_option_data_attributes
