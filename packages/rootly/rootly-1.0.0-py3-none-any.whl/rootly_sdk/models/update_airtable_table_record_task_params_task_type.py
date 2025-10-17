from enum import Enum


class UpdateAirtableTableRecordTaskParamsTaskType(str, Enum):
    UPDATE_AIRTABLE_TABLE_RECORD = "update_airtable_table_record"

    def __str__(self) -> str:
        return str(self.value)
