from enum import Enum


class GetUserInclude(str, Enum):
    DEVICES = "devices"
    EMAIL_ADDRESSES = "email_addresses"
    ON_CALL_ROLE = "on_call_role"
    PHONE_NUMBERS = "phone_numbers"
    ROLE = "role"

    def __str__(self) -> str:
        return str(self.value)
