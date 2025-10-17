from enum import Enum


class CreateAirtableTableRecordTaskParamsTaskType(str, Enum):
    CREATE_AIRTABLE_TABLE_RECORD = "create_airtable_table_record"

    def __str__(self) -> str:
        return str(self.value)
