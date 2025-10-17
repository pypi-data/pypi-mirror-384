from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define

from ..models.new_sub_status_data_attributes_parent_status import NewSubStatusDataAttributesParentStatus
from ..types import UNSET, Unset

T = TypeVar("T", bound="NewSubStatusDataAttributes")


@_attrs_define
class NewSubStatusDataAttributes:
    """
    Attributes:
        name (str):
        parent_status (NewSubStatusDataAttributesParentStatus):
        slug (Union[Unset, str]):
        description (Union[None, Unset, str]):
        position (Union[None, Unset, int]):
    """

    name: str
    parent_status: NewSubStatusDataAttributesParentStatus
    slug: Union[Unset, str] = UNSET
    description: Union[None, Unset, str] = UNSET
    position: Union[None, Unset, int] = UNSET

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        parent_status = self.parent_status.value

        slug = self.slug

        description: Union[None, Unset, str]
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        position: Union[None, Unset, int]
        if isinstance(self.position, Unset):
            position = UNSET
        else:
            position = self.position

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "name": name,
                "parent_status": parent_status,
            }
        )
        if slug is not UNSET:
            field_dict["slug"] = slug
        if description is not UNSET:
            field_dict["description"] = description
        if position is not UNSET:
            field_dict["position"] = position

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        name = d.pop("name")

        parent_status = NewSubStatusDataAttributesParentStatus(d.pop("parent_status"))

        slug = d.pop("slug", UNSET)

        def _parse_description(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        description = _parse_description(d.pop("description", UNSET))

        def _parse_position(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        position = _parse_position(d.pop("position", UNSET))

        new_sub_status_data_attributes = cls(
            name=name,
            parent_status=parent_status,
            slug=slug,
            description=description,
            position=position,
        )

        return new_sub_status_data_attributes
