from enum import Enum


class UpdateGoogleCalendarEventTaskParamsConferenceSolutionKey(str, Enum):
    ADDON = "addOn"
    EVENTHANGOUT = "eventHangout"
    EVENTNAMEDHANGOUT = "eventNamedHangout"
    HANGOUTSMEET = "hangoutsMeet"

    def __str__(self) -> str:
        return str(self.value)
