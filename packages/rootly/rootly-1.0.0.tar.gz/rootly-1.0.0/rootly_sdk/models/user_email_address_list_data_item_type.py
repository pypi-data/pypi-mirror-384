from enum import Enum


class UserEmailAddressListDataItemType(str, Enum):
    USER_EMAIL_ADDRESSES = "user_email_addresses"

    def __str__(self) -> str:
        return str(self.value)
