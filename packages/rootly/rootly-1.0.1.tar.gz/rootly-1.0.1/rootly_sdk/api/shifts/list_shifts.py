from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.errors_list import ErrorsList
from ...models.list_shifts_include import ListShiftsInclude
from ...models.shift_list import ShiftList
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    include: Union[Unset, ListShiftsInclude] = UNSET,
    to: Union[Unset, str] = UNSET,
    from_: Union[Unset, str] = UNSET,
    user_ids: Union[Unset, list[int]] = UNSET,
    schedule_ids: Union[Unset, list[str]] = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    json_include: Union[Unset, str] = UNSET
    if not isinstance(include, Unset):
        json_include = include

    params["include"] = json_include

    params["to"] = to

    params["from"] = from_

    json_user_ids: Union[Unset, list[int]] = UNSET
    if not isinstance(user_ids, Unset):
        json_user_ids = user_ids

    params["user_ids[]"] = json_user_ids

    json_schedule_ids: Union[Unset, list[str]] = UNSET
    if not isinstance(schedule_ids, Unset):
        json_schedule_ids = schedule_ids

    params["schedule_ids[]"] = json_schedule_ids

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v1/shifts",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[ErrorsList, ShiftList]]:
    if response.status_code == 200:
        response_200 = ShiftList.from_dict(response.json())

        return response_200

    if response.status_code == 404:
        response_404 = ErrorsList.from_dict(response.json())

        return response_404

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[ErrorsList, ShiftList]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    include: Union[Unset, ListShiftsInclude] = UNSET,
    to: Union[Unset, str] = UNSET,
    from_: Union[Unset, str] = UNSET,
    user_ids: Union[Unset, list[int]] = UNSET,
    schedule_ids: Union[Unset, list[str]] = UNSET,
) -> Response[Union[ErrorsList, ShiftList]]:
    """List shifts

     List shifts

    Args:
        include (Union[Unset, ListShiftsInclude]):
        to (Union[Unset, str]):
        from_ (Union[Unset, str]):
        user_ids (Union[Unset, list[int]]):
        schedule_ids (Union[Unset, list[str]]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ErrorsList, ShiftList]]
    """

    kwargs = _get_kwargs(
        include=include,
        to=to,
        from_=from_,
        user_ids=user_ids,
        schedule_ids=schedule_ids,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient,
    include: Union[Unset, ListShiftsInclude] = UNSET,
    to: Union[Unset, str] = UNSET,
    from_: Union[Unset, str] = UNSET,
    user_ids: Union[Unset, list[int]] = UNSET,
    schedule_ids: Union[Unset, list[str]] = UNSET,
) -> Optional[Union[ErrorsList, ShiftList]]:
    """List shifts

     List shifts

    Args:
        include (Union[Unset, ListShiftsInclude]):
        to (Union[Unset, str]):
        from_ (Union[Unset, str]):
        user_ids (Union[Unset, list[int]]):
        schedule_ids (Union[Unset, list[str]]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ErrorsList, ShiftList]
    """

    return sync_detailed(
        client=client,
        include=include,
        to=to,
        from_=from_,
        user_ids=user_ids,
        schedule_ids=schedule_ids,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    include: Union[Unset, ListShiftsInclude] = UNSET,
    to: Union[Unset, str] = UNSET,
    from_: Union[Unset, str] = UNSET,
    user_ids: Union[Unset, list[int]] = UNSET,
    schedule_ids: Union[Unset, list[str]] = UNSET,
) -> Response[Union[ErrorsList, ShiftList]]:
    """List shifts

     List shifts

    Args:
        include (Union[Unset, ListShiftsInclude]):
        to (Union[Unset, str]):
        from_ (Union[Unset, str]):
        user_ids (Union[Unset, list[int]]):
        schedule_ids (Union[Unset, list[str]]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ErrorsList, ShiftList]]
    """

    kwargs = _get_kwargs(
        include=include,
        to=to,
        from_=from_,
        user_ids=user_ids,
        schedule_ids=schedule_ids,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    include: Union[Unset, ListShiftsInclude] = UNSET,
    to: Union[Unset, str] = UNSET,
    from_: Union[Unset, str] = UNSET,
    user_ids: Union[Unset, list[int]] = UNSET,
    schedule_ids: Union[Unset, list[str]] = UNSET,
) -> Optional[Union[ErrorsList, ShiftList]]:
    """List shifts

     List shifts

    Args:
        include (Union[Unset, ListShiftsInclude]):
        to (Union[Unset, str]):
        from_ (Union[Unset, str]):
        user_ids (Union[Unset, list[int]]):
        schedule_ids (Union[Unset, list[str]]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ErrorsList, ShiftList]
    """

    return (
        await asyncio_detailed(
            client=client,
            include=include,
            to=to,
            from_=from_,
            user_ids=user_ids,
            schedule_ids=schedule_ids,
        )
    ).parsed
