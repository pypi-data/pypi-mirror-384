from typing import Literal, cast

HttpClientTaskParamsMethod = Literal["DELETE", "GET", "OPTIONS", "PATCH", "POST", "PUT"]

HTTP_CLIENT_TASK_PARAMS_METHOD_VALUES: set[HttpClientTaskParamsMethod] = {
    "DELETE",
    "GET",
    "OPTIONS",
    "PATCH",
    "POST",
    "PUT",
}


def check_http_client_task_params_method(value: str) -> HttpClientTaskParamsMethod:
    if value in HTTP_CLIENT_TASK_PARAMS_METHOD_VALUES:
        return cast(HttpClientTaskParamsMethod, value)
    raise TypeError(f"Unexpected value {value!r}. Expected one of {HTTP_CLIENT_TASK_PARAMS_METHOD_VALUES!r}")
