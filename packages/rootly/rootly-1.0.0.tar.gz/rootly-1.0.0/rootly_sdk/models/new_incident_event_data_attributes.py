from typing import Any, TypeVar, Union

from attrs import define as _attrs_define

from ..models.new_incident_event_data_attributes_visibility import NewIncidentEventDataAttributesVisibility
from ..types import UNSET, Unset

T = TypeVar("T", bound="NewIncidentEventDataAttributes")


@_attrs_define
class NewIncidentEventDataAttributes:
    """
    Attributes:
        event (str): The summary of the incident event
        visibility (Union[Unset, NewIncidentEventDataAttributesVisibility]): The visibility of the incident action item
    """

    event: str
    visibility: Union[Unset, NewIncidentEventDataAttributesVisibility] = UNSET

    def to_dict(self) -> dict[str, Any]:
        event = self.event

        visibility: Union[Unset, str] = UNSET
        if not isinstance(self.visibility, Unset):
            visibility = self.visibility.value

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "event": event,
            }
        )
        if visibility is not UNSET:
            field_dict["visibility"] = visibility

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        event = d.pop("event")

        _visibility = d.pop("visibility", UNSET)
        visibility: Union[Unset, NewIncidentEventDataAttributesVisibility]
        if isinstance(_visibility, Unset):
            visibility = UNSET
        else:
            visibility = NewIncidentEventDataAttributesVisibility(_visibility)

        new_incident_event_data_attributes = cls(
            event=event,
            visibility=visibility,
        )

        return new_incident_event_data_attributes
