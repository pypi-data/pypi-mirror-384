from typing import Literal, cast

GetWorkflowInclude = Literal["form_field_conditions", "genius_tasks", "genius_workflow_runs"]

GET_WORKFLOW_INCLUDE_VALUES: set[GetWorkflowInclude] = {
    "form_field_conditions",
    "genius_tasks",
    "genius_workflow_runs",
}


def check_get_workflow_include(value: str) -> GetWorkflowInclude:
    if value in GET_WORKFLOW_INCLUDE_VALUES:
        return cast(GetWorkflowInclude, value)
    raise TypeError(f"Unexpected value {value!r}. Expected one of {GET_WORKFLOW_INCLUDE_VALUES!r}")
