from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..models.new_incident_event_service_data_attributes_status import NewIncidentEventServiceDataAttributesStatus

T = TypeVar("T", bound="NewIncidentEventServiceDataAttributes")


@_attrs_define
class NewIncidentEventServiceDataAttributes:
    """
    Attributes:
        incident_event_id (str): The ID of the incident event.
        service_id (str): The ID of the service.
        status (NewIncidentEventServiceDataAttributesStatus): The status of the affected service
    """

    incident_event_id: str
    service_id: str
    status: NewIncidentEventServiceDataAttributesStatus

    def to_dict(self) -> dict[str, Any]:
        incident_event_id = self.incident_event_id

        service_id = self.service_id

        status = self.status.value

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "incident_event_id": incident_event_id,
                "service_id": service_id,
                "status": status,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        incident_event_id = d.pop("incident_event_id")

        service_id = d.pop("service_id")

        status = NewIncidentEventServiceDataAttributesStatus(d.pop("status"))

        new_incident_event_service_data_attributes = cls(
            incident_event_id=incident_event_id,
            service_id=service_id,
            status=status,
        )

        return new_incident_event_service_data_attributes
