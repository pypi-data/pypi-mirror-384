from enum import Enum


class SnapshotNewRelicGraphTaskParamsMetricType(str, Enum):
    APDEX = "APDEX"
    AREA = "AREA"
    BAR = "BAR"
    BASELINE = "BASELINE"
    BILLBOARD = "BILLBOARD"
    BULLET = "BULLET"
    EVENT_FEED = "EVENT_FEED"
    FUNNEL = "FUNNEL"
    HEATMAP = "HEATMAP"
    HISTOGRAM = "HISTOGRAM"
    LINE = "LINE"
    PIE = "PIE"
    SCATTER = "SCATTER"
    STACKED_HORIZONTAL_BAR = "STACKED_HORIZONTAL_BAR"
    TABLE = "TABLE"
    VERTICAL_BAR = "VERTICAL_BAR"

    def __str__(self) -> str:
        return str(self.value)
