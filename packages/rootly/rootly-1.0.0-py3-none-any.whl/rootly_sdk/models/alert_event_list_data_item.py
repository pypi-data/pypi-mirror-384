from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.alert_event_list_data_item_type import AlertEventListDataItemType

if TYPE_CHECKING:
    from ..models.alert_event import AlertEvent


T = TypeVar("T", bound="AlertEventListDataItem")


@_attrs_define
class AlertEventListDataItem:
    """
    Attributes:
        id (str): Unique ID of the alert event
        type_ (AlertEventListDataItemType):
        attributes (AlertEvent):
    """

    id: str
    type_: AlertEventListDataItemType
    attributes: "AlertEvent"
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
        from ..models.alert_event import AlertEvent

        d = src_dict.copy()
        id = d.pop("id")

        type_ = AlertEventListDataItemType(d.pop("type"))

        attributes = AlertEvent.from_dict(d.pop("attributes"))

        alert_event_list_data_item = cls(
            id=id,
            type_=type_,
            attributes=attributes,
        )

        alert_event_list_data_item.additional_properties = d
        return alert_event_list_data_item

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
