from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.alert_event_response_data import AlertEventResponseData


T = TypeVar("T", bound="AlertEventResponse")


@_attrs_define
class AlertEventResponse:
    """
    Attributes:
        data (AlertEventResponseData):
    """

    data: "AlertEventResponseData"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = self.data.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "data": data,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        from ..models.alert_event_response_data import AlertEventResponseData

        d = src_dict.copy()
        data = AlertEventResponseData.from_dict(d.pop("data"))

        alert_event_response = cls(
            data=data,
        )

        alert_event_response.additional_properties = d
        return alert_event_response

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
