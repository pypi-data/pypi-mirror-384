from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.update_form_set_condition_data_type import UpdateFormSetConditionDataType

if TYPE_CHECKING:
    from ..models.update_form_set_condition_data_attributes import UpdateFormSetConditionDataAttributes


T = TypeVar("T", bound="UpdateFormSetConditionData")


@_attrs_define
class UpdateFormSetConditionData:
    """
    Attributes:
        type_ (UpdateFormSetConditionDataType):
        attributes (UpdateFormSetConditionDataAttributes):
    """

    type_: UpdateFormSetConditionDataType
    attributes: "UpdateFormSetConditionDataAttributes"
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
        from ..models.update_form_set_condition_data_attributes import UpdateFormSetConditionDataAttributes

        d = src_dict.copy()
        type_ = UpdateFormSetConditionDataType(d.pop("type"))

        attributes = UpdateFormSetConditionDataAttributes.from_dict(d.pop("attributes"))

        update_form_set_condition_data = cls(
            type_=type_,
            attributes=attributes,
        )

        update_form_set_condition_data.additional_properties = d
        return update_form_set_condition_data

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
