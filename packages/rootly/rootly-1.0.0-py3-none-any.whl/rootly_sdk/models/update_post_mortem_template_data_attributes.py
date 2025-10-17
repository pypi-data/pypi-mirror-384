from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define

from ..models.update_post_mortem_template_data_attributes_format import UpdatePostMortemTemplateDataAttributesFormat
from ..types import UNSET, Unset

T = TypeVar("T", bound="UpdatePostMortemTemplateDataAttributes")


@_attrs_define
class UpdatePostMortemTemplateDataAttributes:
    """
    Attributes:
        name (Union[Unset, str]): The name of the postmortem template
        default (Union[None, Unset, bool]): Default selected template when editing a postmortem
        content (Union[Unset, str]): The postmortem template. Liquid syntax is supported
        format_ (Union[Unset, UpdatePostMortemTemplateDataAttributesFormat]): The format of the input Default:
            UpdatePostMortemTemplateDataAttributesFormat.HTML.
    """

    name: Union[Unset, str] = UNSET
    default: Union[None, Unset, bool] = UNSET
    content: Union[Unset, str] = UNSET
    format_: Union[Unset, UpdatePostMortemTemplateDataAttributesFormat] = (
        UpdatePostMortemTemplateDataAttributesFormat.HTML
    )

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        default: Union[None, Unset, bool]
        if isinstance(self.default, Unset):
            default = UNSET
        else:
            default = self.default

        content = self.content

        format_: Union[Unset, str] = UNSET
        if not isinstance(self.format_, Unset):
            format_ = self.format_.value

        field_dict: dict[str, Any] = {}
        field_dict.update({})
        if name is not UNSET:
            field_dict["name"] = name
        if default is not UNSET:
            field_dict["default"] = default
        if content is not UNSET:
            field_dict["content"] = content
        if format_ is not UNSET:
            field_dict["format"] = format_

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        name = d.pop("name", UNSET)

        def _parse_default(data: object) -> Union[None, Unset, bool]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, bool], data)

        default = _parse_default(d.pop("default", UNSET))

        content = d.pop("content", UNSET)

        _format_ = d.pop("format", UNSET)
        format_: Union[Unset, UpdatePostMortemTemplateDataAttributesFormat]
        if isinstance(_format_, Unset):
            format_ = UNSET
        else:
            format_ = UpdatePostMortemTemplateDataAttributesFormat(_format_)

        update_post_mortem_template_data_attributes = cls(
            name=name,
            default=default,
            content=content,
            format_=format_,
        )

        return update_post_mortem_template_data_attributes
