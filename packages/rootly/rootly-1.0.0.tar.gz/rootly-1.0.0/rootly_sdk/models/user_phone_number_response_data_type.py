from enum import Enum


class UserPhoneNumberResponseDataType(str, Enum):
    USER_PHONE_NUMBERS = "user_phone_numbers"

    def __str__(self) -> str:
        return str(self.value)
