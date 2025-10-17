from enum import Enum


class GeneratePhoneNumberLiveCallRouterCountryCode(str, Enum):
    AU = "AU"
    CA = "CA"
    GB = "GB"
    NL = "NL"
    NZ = "NZ"
    US = "US"

    def __str__(self) -> str:
        return str(self.value)
