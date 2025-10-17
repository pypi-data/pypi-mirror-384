from typing import Literal, cast

CreateAirtableTableRecordTaskParamsTaskType = Literal["create_airtable_table_record"]

CREATE_AIRTABLE_TABLE_RECORD_TASK_PARAMS_TASK_TYPE_VALUES: set[CreateAirtableTableRecordTaskParamsTaskType] = {
    "create_airtable_table_record",
}


def check_create_airtable_table_record_task_params_task_type(value: str) -> CreateAirtableTableRecordTaskParamsTaskType:
    if value in CREATE_AIRTABLE_TABLE_RECORD_TASK_PARAMS_TASK_TYPE_VALUES:
        return cast(CreateAirtableTableRecordTaskParamsTaskType, value)
    raise TypeError(
        f"Unexpected value {value!r}. Expected one of {CREATE_AIRTABLE_TABLE_RECORD_TASK_PARAMS_TASK_TYPE_VALUES!r}"
    )
