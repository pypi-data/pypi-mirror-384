from typing import Literal, cast

UpdateWorkflowCustomFieldSelectionDataAttributesIncidentCondition = Literal[
    "ANY", "CONTAINS", "CONTAINS_ALL", "CONTAINS_NONE", "IS", "NONE", "SET", "UNSET"
]

UPDATE_WORKFLOW_CUSTOM_FIELD_SELECTION_DATA_ATTRIBUTES_INCIDENT_CONDITION_VALUES: set[
    UpdateWorkflowCustomFieldSelectionDataAttributesIncidentCondition
] = {
    "ANY",
    "CONTAINS",
    "CONTAINS_ALL",
    "CONTAINS_NONE",
    "IS",
    "NONE",
    "SET",
    "UNSET",
}


def check_update_workflow_custom_field_selection_data_attributes_incident_condition(
    value: str,
) -> UpdateWorkflowCustomFieldSelectionDataAttributesIncidentCondition:
    if value in UPDATE_WORKFLOW_CUSTOM_FIELD_SELECTION_DATA_ATTRIBUTES_INCIDENT_CONDITION_VALUES:
        return cast(UpdateWorkflowCustomFieldSelectionDataAttributesIncidentCondition, value)
    raise TypeError(
        f"Unexpected value {value!r}. Expected one of {UPDATE_WORKFLOW_CUSTOM_FIELD_SELECTION_DATA_ATTRIBUTES_INCIDENT_CONDITION_VALUES!r}"
    )
