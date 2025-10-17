from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.workflow_custom_field_selection_incident_condition import WorkflowCustomFieldSelectionIncidentCondition
from ..types import UNSET, Unset

T = TypeVar("T", bound="WorkflowCustomFieldSelection")


@_attrs_define
class WorkflowCustomFieldSelection:
    """
    Attributes:
        workflow_id (str): The workflow for this selection
        custom_field_id (int): The custom field for this selection
        incident_condition (WorkflowCustomFieldSelectionIncidentCondition): The trigger condition Default:
            WorkflowCustomFieldSelectionIncidentCondition.ANY.
        selected_option_ids (list[int]):
        values (Union[Unset, list[str]]):
    """

    workflow_id: str
    custom_field_id: int
    selected_option_ids: list[int]
    incident_condition: WorkflowCustomFieldSelectionIncidentCondition = (
        WorkflowCustomFieldSelectionIncidentCondition.ANY
    )
    values: Union[Unset, list[str]] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        workflow_id = self.workflow_id

        custom_field_id = self.custom_field_id

        incident_condition = self.incident_condition.value

        selected_option_ids = self.selected_option_ids

        values: Union[Unset, list[str]] = UNSET
        if not isinstance(self.values, Unset):
            values = self.values

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "workflow_id": workflow_id,
                "custom_field_id": custom_field_id,
                "incident_condition": incident_condition,
                "selected_option_ids": selected_option_ids,
            }
        )
        if values is not UNSET:
            field_dict["values"] = values

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        workflow_id = d.pop("workflow_id")

        custom_field_id = d.pop("custom_field_id")

        incident_condition = WorkflowCustomFieldSelectionIncidentCondition(d.pop("incident_condition"))

        selected_option_ids = cast(list[int], d.pop("selected_option_ids"))

        values = cast(list[str], d.pop("values", UNSET))

        workflow_custom_field_selection = cls(
            workflow_id=workflow_id,
            custom_field_id=custom_field_id,
            incident_condition=incident_condition,
            selected_option_ids=selected_option_ids,
            values=values,
        )

        workflow_custom_field_selection.additional_properties = d
        return workflow_custom_field_selection

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
