from typing import Any, TypeVar, Union

from attrs import define as _attrs_define

from ..models.update_incident_event_data_attributes_visibility import UpdateIncidentEventDataAttributesVisibility
from ..types import UNSET, Unset

T = TypeVar("T", bound="UpdateIncidentEventDataAttributes")


@_attrs_define
class UpdateIncidentEventDataAttributes:
    """
    Attributes:
        event (Union[Unset, str]): The summary of the incident event
        visibility (Union[Unset, UpdateIncidentEventDataAttributesVisibility]): The visibility of the incident action
            item
    """

    event: Union[Unset, str] = UNSET
    visibility: Union[Unset, UpdateIncidentEventDataAttributesVisibility] = UNSET

    def to_dict(self) -> dict[str, Any]:
        event = self.event

        visibility: Union[Unset, str] = UNSET
        if not isinstance(self.visibility, Unset):
            visibility = self.visibility.value

        field_dict: dict[str, Any] = {}
        field_dict.update({})
        if event is not UNSET:
            field_dict["event"] = event
        if visibility is not UNSET:
            field_dict["visibility"] = visibility

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        event = d.pop("event", UNSET)

        _visibility = d.pop("visibility", UNSET)
        visibility: Union[Unset, UpdateIncidentEventDataAttributesVisibility]
        if isinstance(_visibility, Unset):
            visibility = UNSET
        else:
            visibility = UpdateIncidentEventDataAttributesVisibility(_visibility)

        update_incident_event_data_attributes = cls(
            event=event,
            visibility=visibility,
        )

        return update_incident_event_data_attributes
