from typing import Literal, cast

NewPlaybookDataType = Literal["playbooks"]

NEW_PLAYBOOK_DATA_TYPE_VALUES: set[NewPlaybookDataType] = {
    "playbooks",
}


def check_new_playbook_data_type(value: str) -> NewPlaybookDataType:
    if value in NEW_PLAYBOOK_DATA_TYPE_VALUES:
        return cast(NewPlaybookDataType, value)
    raise TypeError(f"Unexpected value {value!r}. Expected one of {NEW_PLAYBOOK_DATA_TYPE_VALUES!r}")
