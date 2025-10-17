from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="UpdateCommunicationsTypeDataAttributes")


@_attrs_define
class UpdateCommunicationsTypeDataAttributes:
    """
    Attributes:
        name (Union[Unset, str]): The name of the communications type
        description (Union[None, Unset, str]): The description of the communications type
        color (Union[None, Unset, str]): The color of the communications type
        position (Union[None, Unset, int]): Position of the communications type
    """

    name: Union[Unset, str] = UNSET
    description: Union[None, Unset, str] = UNSET
    color: Union[None, Unset, str] = UNSET
    position: Union[None, Unset, int] = UNSET

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        description: Union[None, Unset, str]
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        color: Union[None, Unset, str]
        if isinstance(self.color, Unset):
            color = UNSET
        else:
            color = self.color

        position: Union[None, Unset, int]
        if isinstance(self.position, Unset):
            position = UNSET
        else:
            position = self.position

        field_dict: dict[str, Any] = {}
        field_dict.update({})
        if name is not UNSET:
            field_dict["name"] = name
        if description is not UNSET:
            field_dict["description"] = description
        if color is not UNSET:
            field_dict["color"] = color
        if position is not UNSET:
            field_dict["position"] = position

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        name = d.pop("name", UNSET)

        def _parse_description(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        description = _parse_description(d.pop("description", UNSET))

        def _parse_color(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        color = _parse_color(d.pop("color", UNSET))

        def _parse_position(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        position = _parse_position(d.pop("position", UNSET))

        update_communications_type_data_attributes = cls(
            name=name,
            description=description,
            color=color,
            position=position,
        )

        return update_communications_type_data_attributes
