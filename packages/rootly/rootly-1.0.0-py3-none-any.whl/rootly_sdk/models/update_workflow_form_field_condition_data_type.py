from enum import Enum


class UpdateWorkflowFormFieldConditionDataType(str, Enum):
    WORKFLOW_FORM_FIELD_CONDITIONS = "workflow_form_field_conditions"

    def __str__(self) -> str:
        return str(self.value)
