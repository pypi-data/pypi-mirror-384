from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define

from ..models.update_custom_field_data_attributes_required_type_0_item import (
    UpdateCustomFieldDataAttributesRequiredType0Item,
    check_update_custom_field_data_attributes_required_type_0_item,
)
from ..models.update_custom_field_data_attributes_shown_item import (
    UpdateCustomFieldDataAttributesShownItem,
    check_update_custom_field_data_attributes_shown_item,
)
from ..types import UNSET, Unset

T = TypeVar("T", bound="UpdateCustomFieldDataAttributes")


@_attrs_define
class UpdateCustomFieldDataAttributes:
    """
    Attributes:
        label (Union[Unset, str]): The name of the custom_field
        slug (Union[Unset, str]): The slug of the custom_field
        description (Union[None, Unset, str]): The description of the custom_field
        shown (Union[Unset, list[UpdateCustomFieldDataAttributesShownItem]]):
        required (Union[None, Unset, list[UpdateCustomFieldDataAttributesRequiredType0Item]]):
        default (Union[None, Unset, str]): The default value for text field kinds
        position (Union[Unset, int]): The position of the custom_field
    """

    label: Union[Unset, str] = UNSET
    slug: Union[Unset, str] = UNSET
    description: Union[None, Unset, str] = UNSET
    shown: Union[Unset, list[UpdateCustomFieldDataAttributesShownItem]] = UNSET
    required: Union[None, Unset, list[UpdateCustomFieldDataAttributesRequiredType0Item]] = UNSET
    default: Union[None, Unset, str] = UNSET
    position: Union[Unset, int] = UNSET

    def to_dict(self) -> dict[str, Any]:
        label = self.label

        slug = self.slug

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

        field_dict.update({})
        if label is not UNSET:
            field_dict["label"] = label
        if slug is not UNSET:
            field_dict["slug"] = slug
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
        label = d.pop("label", UNSET)

        slug = d.pop("slug", UNSET)

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
            shown_item = check_update_custom_field_data_attributes_shown_item(shown_item_data)

            shown.append(shown_item)

        def _parse_required(data: object) -> Union[None, Unset, list[UpdateCustomFieldDataAttributesRequiredType0Item]]:
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
                    required_type_0_item = check_update_custom_field_data_attributes_required_type_0_item(
                        required_type_0_item_data
                    )

                    required_type_0.append(required_type_0_item)

                return required_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list[UpdateCustomFieldDataAttributesRequiredType0Item]], data)

        required = _parse_required(d.pop("required", UNSET))

        def _parse_default(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        default = _parse_default(d.pop("default", UNSET))

        position = d.pop("position", UNSET)

        update_custom_field_data_attributes = cls(
            label=label,
            slug=slug,
            description=description,
            shown=shown,
            required=required,
            default=default,
            position=position,
        )

        return update_custom_field_data_attributes
