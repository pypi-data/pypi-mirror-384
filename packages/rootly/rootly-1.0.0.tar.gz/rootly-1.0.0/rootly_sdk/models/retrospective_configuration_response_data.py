from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.retrospective_configuration_response_data_type import RetrospectiveConfigurationResponseDataType

if TYPE_CHECKING:
    from ..models.retrospective_configuration import RetrospectiveConfiguration


T = TypeVar("T", bound="RetrospectiveConfigurationResponseData")


@_attrs_define
class RetrospectiveConfigurationResponseData:
    """
    Attributes:
        id (str): Unique ID of the retrospective configuration
        type_ (RetrospectiveConfigurationResponseDataType):
        attributes (RetrospectiveConfiguration):
    """

    id: str
    type_: RetrospectiveConfigurationResponseDataType
    attributes: "RetrospectiveConfiguration"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        type_ = self.type_.value

        attributes = self.attributes.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "type": type_,
                "attributes": attributes,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        from ..models.retrospective_configuration import RetrospectiveConfiguration

        d = src_dict.copy()
        id = d.pop("id")

        type_ = RetrospectiveConfigurationResponseDataType(d.pop("type"))

        attributes = RetrospectiveConfiguration.from_dict(d.pop("attributes"))

        retrospective_configuration_response_data = cls(
            id=id,
            type_=type_,
            attributes=attributes,
        )

        retrospective_configuration_response_data.additional_properties = d
        return retrospective_configuration_response_data

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
