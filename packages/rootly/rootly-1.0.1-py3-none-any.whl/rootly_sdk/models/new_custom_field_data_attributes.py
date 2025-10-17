from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define

from ..models.new_custom_field_data_attributes_required_type_0_item import (
    NewCustomFieldDataAttributesRequiredType0Item,
    check_new_custom_field_data_attributes_required_type_0_item,
)
from ..models.new_custom_field_data_attributes_shown_item import (
    NewCustomFieldDataAttributesShownItem,
    check_new_custom_field_data_attributes_shown_item,
)
from ..types import UNSET, Unset

T = TypeVar("T", bound="NewCustomFieldDataAttributes")


@_attrs_define
class NewCustomFieldDataAttributes:
    """
    Attributes:
        label (str): The name of the custom_field
        description (Union[None, Unset, str]): The description of the custom_field
        shown (Union[Unset, list[NewCustomFieldDataAttributesShownItem]]):
        required (Union[None, Unset, list[NewCustomFieldDataAttributesRequiredType0Item]]):
        default (Union[None, Unset, str]): The default value for text field kinds
        position (Union[Unset, int]): The position of the custom_field
    """

    label: str
    description: Union[None, Unset, str] = UNSET
    shown: Union[Unset, list[NewCustomFieldDataAttributesShownItem]] = UNSET
    required: Union[None, Unset, list[NewCustomFieldDataAttributesRequiredType0Item]] = UNSET
    default: Union[None, Unset, str] = UNSET
    position: Union[Unset, int] = UNSET

    def to_dict(self) -> dict[str, Any]:
        label = self.label

        description: Union[None, Unset, str]
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        shown: Union[Unset, list[str]] = UNSET
        if not isinstance(self.shown, Unset):
            shown = []
            for shown_item_data in self.shown:
                shown_item: str = shown_item_data
                shown.append(shown_item)

        required: Union[None, Unset, list[str]]
        if isinstance(self.required, Unset):
            required = UNSET
        elif isinstance(self.required, list):
            required = []
            for required_type_0_item_data in self.required:
                required_type_0_item: str = required_type_0_item_data
                required.append(required_type_0_item)

        else:
            required = self.required

        default: Union[None, Unset, str]
        if isinstance(self.default, Unset):
            default = UNSET
        else:
            default = self.default

        position = self.position

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "label": label,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description
        if shown is not UNSET:
            field_dict["shown"] = shown
        if required is not UNSET:
            field_dict["required"] = required
        if default is not UNSET:
            field_dict["default"] = default
        if position is not UNSET:
            field_dict["position"] = position

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        label = d.pop("label")

        def _parse_description(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        description = _parse_description(d.pop("description", UNSET))

        shown = []
        _shown = d.pop("shown", UNSET)
        for shown_item_data in _shown or []:
            shown_item = check_new_custom_field_data_attributes_shown_item(shown_item_data)

            shown.append(shown_item)

        def _parse_required(data: object) -> Union[None, Unset, list[NewCustomFieldDataAttributesRequiredType0Item]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                required_type_0 = []
                _required_type_0 = data
                for required_type_0_item_data in _required_type_0:
                    required_type_0_item = check_new_custom_field_data_attributes_required_type_0_item(
                        required_type_0_item_data
                    )

                    required_type_0.append(required_type_0_item)

                return required_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list[NewCustomFieldDataAttributesRequiredType0Item]], data)

        required = _parse_required(d.pop("required", UNSET))

        def _parse_default(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        default = _parse_default(d.pop("default", UNSET))

        position = d.pop("position", UNSET)

        new_custom_field_data_attributes = cls(
            label=label,
            description=description,
            shown=shown,
            required=required,
            default=default,
            position=position,
        )

        return new_custom_field_data_attributes
