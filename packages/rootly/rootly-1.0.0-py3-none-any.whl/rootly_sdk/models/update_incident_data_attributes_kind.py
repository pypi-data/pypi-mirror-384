from enum import Enum


class UpdateIncidentDataAttributesKind(str, Enum):
    BACKFILLED = "backfilled"
    EXAMPLE = "example"
    EXAMPLE_SUB = "example_sub"
    NORMAL = "normal"
    NORMAL_SUB = "normal_sub"
    SCHEDULED = "scheduled"
    TEST = "test"
    TEST_SUB = "test_sub"

    def __str__(self) -> str:
        return str(self.value)
