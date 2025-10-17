from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..models.incident_event_functionality_status import IncidentEventFunctionalityStatus

T = TypeVar("T", bound="IncidentEventFunctionality")


@_attrs_define
class IncidentEventFunctionality:
    """
    Attributes:
        incident_event_id (str): The ID of the incident event.
        functionality_id (str): The ID of the functionality.
        status (IncidentEventFunctionalityStatus): The status of the affected functionality
    """

    incident_event_id: str
    functionality_id: str
    status: IncidentEventFunctionalityStatus

    def to_dict(self) -> dict[str, Any]:
        incident_event_id = self.incident_event_id

        functionality_id = self.functionality_id

        status = self.status.value

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "incident_event_id": incident_event_id,
                "functionality_id": functionality_id,
                "status": status,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        incident_event_id = d.pop("incident_event_id")

        functionality_id = d.pop("functionality_id")

        status = IncidentEventFunctionalityStatus(d.pop("status"))

        incident_event_functionality = cls(
            incident_event_id=incident_event_id,
            functionality_id=functionality_id,
            status=status,
        )

        return incident_event_functionality
