from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define

from ..models.new_workflow_custom_field_selection_data_attributes_incident_condition import (
    NewWorkflowCustomFieldSelectionDataAttributesIncidentCondition,
)
from ..types import UNSET, Unset

T = TypeVar("T", bound="NewWorkflowCustomFieldSelectionDataAttributes")


@_attrs_define
class NewWorkflowCustomFieldSelectionDataAttributes:
    """
    Attributes:
        custom_field_id (int): The custom field for this selection
        incident_condition (NewWorkflowCustomFieldSelectionDataAttributesIncidentCondition): The trigger condition
            Default: NewWorkflowCustomFieldSelectionDataAttributesIncidentCondition.ANY.
        workflow_id (Union[Unset, str]): The workflow for this selection
        values (Union[Unset, list[str]]):
        selected_option_ids (Union[Unset, list[int]]):
    """

    custom_field_id: int
    incident_condition: NewWorkflowCustomFieldSelectionDataAttributesIncidentCondition = (
        NewWorkflowCustomFieldSelectionDataAttributesIncidentCondition.ANY
    )
    workflow_id: Union[Unset, str] = UNSET
    values: Union[Unset, list[str]] = UNSET
    selected_option_ids: Union[Unset, list[int]] = UNSET

    def to_dict(self) -> dict[str, Any]:
        custom_field_id = self.custom_field_id

        incident_condition = self.incident_condition.value

        workflow_id = self.workflow_id

        values: Union[Unset, list[str]] = UNSET
        if not isinstance(self.values, Unset):
            values = self.values

        selected_option_ids: Union[Unset, list[int]] = UNSET
        if not isinstance(self.selected_option_ids, Unset):
            selected_option_ids = self.selected_option_ids

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "custom_field_id": custom_field_id,
                "incident_condition": incident_condition,
            }
        )
        if workflow_id is not UNSET:
            field_dict["workflow_id"] = workflow_id
        if values is not UNSET:
            field_dict["values"] = values
        if selected_option_ids is not UNSET:
            field_dict["selected_option_ids"] = selected_option_ids

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        custom_field_id = d.pop("custom_field_id")

        incident_condition = NewWorkflowCustomFieldSelectionDataAttributesIncidentCondition(d.pop("incident_condition"))

        workflow_id = d.pop("workflow_id", UNSET)

        values = cast(list[str], d.pop("values", UNSET))

        selected_option_ids = cast(list[int], d.pop("selected_option_ids", UNSET))

        new_workflow_custom_field_selection_data_attributes = cls(
            custom_field_id=custom_field_id,
            incident_condition=incident_condition,
            workflow_id=workflow_id,
            values=values,
            selected_option_ids=selected_option_ids,
        )

        return new_workflow_custom_field_selection_data_attributes
