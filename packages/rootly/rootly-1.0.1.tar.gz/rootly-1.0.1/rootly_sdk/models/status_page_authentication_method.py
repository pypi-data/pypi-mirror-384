from typing import Literal, cast

StatusPageAuthenticationMethod = Literal["none", "password", "saml"]

STATUS_PAGE_AUTHENTICATION_METHOD_VALUES: set[StatusPageAuthenticationMethod] = {
    "none",
    "password",
    "saml",
}


def check_status_page_authentication_method(value: str) -> StatusPageAuthenticationMethod:
    if value in STATUS_PAGE_AUTHENTICATION_METHOD_VALUES:
        return cast(StatusPageAuthenticationMethod, value)
    raise TypeError(f"Unexpected value {value!r}. Expected one of {STATUS_PAGE_AUTHENTICATION_METHOD_VALUES!r}")
