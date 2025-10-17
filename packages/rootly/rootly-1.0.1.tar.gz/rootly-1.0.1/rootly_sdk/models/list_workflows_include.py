from typing import Literal, cast

ListWorkflowsInclude = Literal["form_field_conditions", "genius_tasks", "genius_workflow_runs"]

LIST_WORKFLOWS_INCLUDE_VALUES: set[ListWorkflowsInclude] = {
    "form_field_conditions",
    "genius_tasks",
    "genius_workflow_runs",
}


def check_list_workflows_include(value: str) -> ListWorkflowsInclude:
    if value in LIST_WORKFLOWS_INCLUDE_VALUES:
        return cast(ListWorkflowsInclude, value)
    raise TypeError(f"Unexpected value {value!r}. Expected one of {LIST_WORKFLOWS_INCLUDE_VALUES!r}")
