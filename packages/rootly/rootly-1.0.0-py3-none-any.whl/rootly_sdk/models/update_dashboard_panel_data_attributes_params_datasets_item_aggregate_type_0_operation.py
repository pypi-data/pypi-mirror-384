from enum import Enum


class UpdateDashboardPanelDataAttributesParamsDatasetsItemAggregateType0Operation(str, Enum):
    AVERAGE = "average"
    COUNT = "count"
    SUM = "sum"

    def __str__(self) -> str:
        return str(self.value)
