from enum import Enum


class HttpClientTaskParamsTaskType(str, Enum):
    HTTP_CLIENT = "http_client"

    def __str__(self) -> str:
        return str(self.value)
