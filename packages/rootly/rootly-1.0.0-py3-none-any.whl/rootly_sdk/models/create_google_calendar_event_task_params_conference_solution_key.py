from enum import Enum


class CreateGoogleCalendarEventTaskParamsConferenceSolutionKey(str, Enum):
    ADDON = "addOn"
    EVENTHANGOUT = "eventHangout"
    EVENTNAMEDHANGOUT = "eventNamedHangout"
    HANGOUTSMEET = "hangoutsMeet"

    def __str__(self) -> str:
        return str(self.value)
