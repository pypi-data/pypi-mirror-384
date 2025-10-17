from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.alert_field_response_data_type import AlertFieldResponseDataType, check_alert_field_response_data_type
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.alert_field import AlertField


T = TypeVar("T", bound="AlertFieldResponseData")


@_attrs_define
class AlertFieldResponseData:
    """
    Attributes:
        type_ (AlertFieldResponseDataType):
        attributes (AlertField):
        id (Union[Unset, str]): The ID of the alert field
    """

    type_: AlertFieldResponseDataType
    attributes: "AlertField"
    id: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        type_: str = self.type_

        attributes = self.attributes.to_dict()

        id = self.id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "type": type_,
                "attributes": attributes,
            }
        )
        if id is not UNSET:
            field_dict["id"] = id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.alert_field import AlertField

        d = dict(src_dict)
        type_ = check_alert_field_response_data_type(d.pop("type"))

        attributes = AlertField.from_dict(d.pop("attributes"))

        id = d.pop("id", UNSET)

        alert_field_response_data = cls(
            type_=type_,
            attributes=attributes,
            id=id,
        )

        alert_field_response_data.additional_properties = d
        return alert_field_response_data

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
