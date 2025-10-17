from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="UpdateServiceDataAttributesSlackChannelsType0Item")


@_attrs_define
class UpdateServiceDataAttributesSlackChannelsType0Item:
    """
    Attributes:
        id (str): Slack channel ID
        name (str): Slack channel name
    """

    id: str
    name: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        name = self.name

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        id = d.pop("id")

        name = d.pop("name")

        update_service_data_attributes_slack_channels_type_0_item = cls(
            id=id,
            name=name,
        )

        update_service_data_attributes_slack_channels_type_0_item.additional_properties = d
        return update_service_data_attributes_slack_channels_type_0_item

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
