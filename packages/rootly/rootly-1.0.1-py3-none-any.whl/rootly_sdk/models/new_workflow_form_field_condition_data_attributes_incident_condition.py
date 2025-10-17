from typing import Literal, cast

NewWorkflowFormFieldConditionDataAttributesIncidentCondition = Literal[
    "ANY", "CONTAINS", "CONTAINS_ALL", "CONTAINS_NONE", "IS", "NONE", "SET", "UNSET"
]

NEW_WORKFLOW_FORM_FIELD_CONDITION_DATA_ATTRIBUTES_INCIDENT_CONDITION_VALUES: set[
    NewWorkflowFormFieldConditionDataAttributesIncidentCondition
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


def check_new_workflow_form_field_condition_data_attributes_incident_condition(
    value: str,
) -> NewWorkflowFormFieldConditionDataAttributesIncidentCondition:
    if value in NEW_WORKFLOW_FORM_FIELD_CONDITION_DATA_ATTRIBUTES_INCIDENT_CONDITION_VALUES:
        return cast(NewWorkflowFormFieldConditionDataAttributesIncidentCondition, value)
    raise TypeError(
        f"Unexpected value {value!r}. Expected one of {NEW_WORKFLOW_FORM_FIELD_CONDITION_DATA_ATTRIBUTES_INCIDENT_CONDITION_VALUES!r}"
    )
