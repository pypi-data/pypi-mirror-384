from enum import IntEnum


class NewIncidentFeedbackDataAttributesRating(IntEnum):
    VALUE_4 = 4
    VALUE_3 = 3
    VALUE_2 = 2
    VALUE_1 = 1
    VALUE_0 = 0

    def __str__(self) -> str:
        return str(self.value)
