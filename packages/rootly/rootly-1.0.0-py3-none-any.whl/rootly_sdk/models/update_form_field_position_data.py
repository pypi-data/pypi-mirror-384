from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.update_form_field_position_data_type import UpdateFormFieldPositionDataType

if TYPE_CHECKING:
    from ..models.update_form_field_position_data_attributes import UpdateFormFieldPositionDataAttributes


T = TypeVar("T", bound="UpdateFormFieldPositionData")


@_attrs_define
class UpdateFormFieldPositionData:
    """
    Attributes:
        type_ (UpdateFormFieldPositionDataType):
        attributes (UpdateFormFieldPositionDataAttributes):
    """

    type_: UpdateFormFieldPositionDataType
    attributes: "UpdateFormFieldPositionDataAttributes"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        type_ = self.type_.value

        attributes = self.attributes.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "type": type_,
                "attributes": attributes,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        from ..models.update_form_field_position_data_attributes import UpdateFormFieldPositionDataAttributes

        d = src_dict.copy()
        type_ = UpdateFormFieldPositionDataType(d.pop("type"))

        attributes = UpdateFormFieldPositionDataAttributes.from_dict(d.pop("attributes"))

        update_form_field_position_data = cls(
            type_=type_,
            attributes=attributes,
        )

        update_form_field_position_data.additional_properties = d
        return update_form_field_position_data

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
