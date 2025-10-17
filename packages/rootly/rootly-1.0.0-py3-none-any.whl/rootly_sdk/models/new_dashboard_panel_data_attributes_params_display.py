from enum import Enum


class NewDashboardPanelDataAttributesParamsDisplay(str, Enum):
    AGGREGATE_VALUE = "aggregate_value"
    COLUMN_CHART = "column_chart"
    LINE_CHART = "line_chart"
    LINE_STEPPED_CHART = "line_stepped_chart"
    MONITORING_CHART = "monitoring_chart"
    PIE_CHART = "pie_chart"
    STACKED_COLUMN_CHART = "stacked_column_chart"
    TABLE = "table"

    def __str__(self) -> str:
        return str(self.value)
