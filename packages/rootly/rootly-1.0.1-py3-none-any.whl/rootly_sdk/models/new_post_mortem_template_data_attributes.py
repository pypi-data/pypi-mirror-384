from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define

from ..models.new_post_mortem_template_data_attributes_format import (
    NewPostMortemTemplateDataAttributesFormat,
    check_new_post_mortem_template_data_attributes_format,
)
from ..types import UNSET, Unset

T = TypeVar("T", bound="NewPostMortemTemplateDataAttributes")


@_attrs_define
class NewPostMortemTemplateDataAttributes:
    """
    Attributes:
        name (str): The name of the postmortem template
        content (str): The postmortem template. Liquid syntax is supported
        default (Union[None, Unset, bool]): Default selected template when editing a postmortem
        format_ (Union[Unset, NewPostMortemTemplateDataAttributesFormat]): The format of the input Default: 'html'.
    """

    name: str
    content: str
    default: Union[None, Unset, bool] = UNSET
    format_: Union[Unset, NewPostMortemTemplateDataAttributesFormat] = "html"

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        content = self.content

        default: Union[None, Unset, bool]
        if isinstance(self.default, Unset):
            default = UNSET
        else:
            default = self.default

        format_: Union[Unset, str] = UNSET
        if not isinstance(self.format_, Unset):
            format_ = self.format_

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "name": name,
                "content": content,
            }
        )
        if default is not UNSET:
            field_dict["default"] = default
        if format_ is not UNSET:
            field_dict["format"] = format_

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        content = d.pop("content")

        def _parse_default(data: object) -> Union[None, Unset, bool]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, bool], data)

        default = _parse_default(d.pop("default", UNSET))

        _format_ = d.pop("format", UNSET)
        format_: Union[Unset, NewPostMortemTemplateDataAttributesFormat]
        if isinstance(_format_, Unset):
            format_ = UNSET
        else:
            format_ = check_new_post_mortem_template_data_attributes_format(_format_)

        new_post_mortem_template_data_attributes = cls(
            name=name,
            content=content,
            default=default,
            format_=format_,
        )

        return new_post_mortem_template_data_attributes
