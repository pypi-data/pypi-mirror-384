from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.post_mortem_template_format import PostMortemTemplateFormat
from ..types import UNSET, Unset

T = TypeVar("T", bound="PostMortemTemplate")


@_attrs_define
class PostMortemTemplate:
    """
    Attributes:
        name (str): The name of the postmortem template
        created_at (str): Date of creation
        updated_at (str): Date of last update
        slug (Union[Unset, str]): The slugified name of the postmortem template
        default (Union[None, Unset, bool]): Default selected template when editing a postmortem
        content (Union[Unset, str]): The postmortem template. Liquid syntax and markdown are supported
        format_ (Union[Unset, PostMortemTemplateFormat]): The format of the input
    """

    name: str
    created_at: str
    updated_at: str
    slug: Union[Unset, str] = UNSET
    default: Union[None, Unset, bool] = UNSET
    content: Union[Unset, str] = UNSET
    format_: Union[Unset, PostMortemTemplateFormat] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        created_at = self.created_at

        updated_at = self.updated_at

        slug = self.slug

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
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "created_at": created_at,
                "updated_at": updated_at,
            }
        )
        if slug is not UNSET:
            field_dict["slug"] = slug
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
        name = d.pop("name")

        created_at = d.pop("created_at")

        updated_at = d.pop("updated_at")

        slug = d.pop("slug", UNSET)

        def _parse_default(data: object) -> Union[None, Unset, bool]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, bool], data)

        default = _parse_default(d.pop("default", UNSET))

        content = d.pop("content", UNSET)

        _format_ = d.pop("format", UNSET)
        format_: Union[Unset, PostMortemTemplateFormat]
        if isinstance(_format_, Unset):
            format_ = UNSET
        else:
            format_ = PostMortemTemplateFormat(_format_)

        post_mortem_template = cls(
            name=name,
            created_at=created_at,
            updated_at=updated_at,
            slug=slug,
            default=default,
            content=content,
            format_=format_,
        )

        post_mortem_template.additional_properties = d
        return post_mortem_template

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
