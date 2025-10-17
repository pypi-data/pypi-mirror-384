from typing import Literal, cast

SubStatusParentStatus = Literal[
    "cancelled",
    "closed",
    "completed",
    "in_progress",
    "in_triage",
    "planning",
    "resolved",
    "scheduled",
    "started",
    "verifying",
]

SUB_STATUS_PARENT_STATUS_VALUES: set[SubStatusParentStatus] = {
    "cancelled",
    "closed",
    "completed",
    "in_progress",
    "in_triage",
    "planning",
    "resolved",
    "scheduled",
    "started",
    "verifying",
}


def check_sub_status_parent_status(value: str) -> SubStatusParentStatus:
    if value in SUB_STATUS_PARENT_STATUS_VALUES:
        return cast(SubStatusParentStatus, value)
    raise TypeError(f"Unexpected value {value!r}. Expected one of {SUB_STATUS_PARENT_STATUS_VALUES!r}")
