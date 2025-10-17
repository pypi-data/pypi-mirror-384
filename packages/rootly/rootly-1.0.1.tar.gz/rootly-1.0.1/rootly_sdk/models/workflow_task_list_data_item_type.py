from typing import Literal, cast

WorkflowTaskListDataItemType = Literal["workflow_tasks"]

WORKFLOW_TASK_LIST_DATA_ITEM_TYPE_VALUES: set[WorkflowTaskListDataItemType] = {
    "workflow_tasks",
}


def check_workflow_task_list_data_item_type(value: str) -> WorkflowTaskListDataItemType:
    if value in WORKFLOW_TASK_LIST_DATA_ITEM_TYPE_VALUES:
        return cast(WorkflowTaskListDataItemType, value)
    raise TypeError(f"Unexpected value {value!r}. Expected one of {WORKFLOW_TASK_LIST_DATA_ITEM_TYPE_VALUES!r}")
