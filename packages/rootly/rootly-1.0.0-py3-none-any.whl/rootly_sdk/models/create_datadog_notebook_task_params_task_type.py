from enum import Enum


class CreateDatadogNotebookTaskParamsTaskType(str, Enum):
    CREATE_DATADOG_NOTEBOOK = "create_datadog_notebook"

    def __str__(self) -> str:
        return str(self.value)
