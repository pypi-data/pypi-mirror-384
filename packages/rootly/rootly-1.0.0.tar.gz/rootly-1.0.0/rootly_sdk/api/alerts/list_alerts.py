from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.alert_list import AlertList
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    include: Union[Unset, str] = UNSET,
    filterstatus: Union[Unset, str] = UNSET,
    pagenumber: Union[Unset, int] = UNSET,
    pagesize: Union[Unset, int] = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["include"] = include

    params["filter[status]"] = filterstatus

    params["page[number]"] = pagenumber

    params["page[size]"] = pagesize

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v1/alerts",
        "params": params,
    }

    return _kwargs


def _parse_response(*, client: Union[AuthenticatedClient, Client], response: httpx.Response) -> Optional[AlertList]:
    if response.status_code == 200:
        response_200 = AlertList.from_dict(response.json())

        return response_200
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(*, client: Union[AuthenticatedClient, Client], response: httpx.Response) -> Response[AlertList]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    include: Union[Unset, str] = UNSET,
    filterstatus: Union[Unset, str] = UNSET,
    pagenumber: Union[Unset, int] = UNSET,
    pagesize: Union[Unset, int] = UNSET,
) -> Response[AlertList]:
    """List alerts

     List alerts

    Args:
        include (Union[Unset, str]):
        filterstatus (Union[Unset, str]):
        pagenumber (Union[Unset, int]):
        pagesize (Union[Unset, int]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AlertList]
    """

    kwargs = _get_kwargs(
        include=include,
        filterstatus=filterstatus,
        pagenumber=pagenumber,
        pagesize=pagesize,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient,
    include: Union[Unset, str] = UNSET,
    filterstatus: Union[Unset, str] = UNSET,
    pagenumber: Union[Unset, int] = UNSET,
    pagesize: Union[Unset, int] = UNSET,
) -> Optional[AlertList]:
    """List alerts

     List alerts

    Args:
        include (Union[Unset, str]):
        filterstatus (Union[Unset, str]):
        pagenumber (Union[Unset, int]):
        pagesize (Union[Unset, int]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AlertList
    """

    return sync_detailed(
        client=client,
        include=include,
        filterstatus=filterstatus,
        pagenumber=pagenumber,
        pagesize=pagesize,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    include: Union[Unset, str] = UNSET,
    filterstatus: Union[Unset, str] = UNSET,
    pagenumber: Union[Unset, int] = UNSET,
    pagesize: Union[Unset, int] = UNSET,
) -> Response[AlertList]:
    """List alerts

     List alerts

    Args:
        include (Union[Unset, str]):
        filterstatus (Union[Unset, str]):
        pagenumber (Union[Unset, int]):
        pagesize (Union[Unset, int]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AlertList]
    """

    kwargs = _get_kwargs(
        include=include,
        filterstatus=filterstatus,
        pagenumber=pagenumber,
        pagesize=pagesize,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    include: Union[Unset, str] = UNSET,
    filterstatus: Union[Unset, str] = UNSET,
    pagenumber: Union[Unset, int] = UNSET,
    pagesize: Union[Unset, int] = UNSET,
) -> Optional[AlertList]:
    """List alerts

     List alerts

    Args:
        include (Union[Unset, str]):
        filterstatus (Union[Unset, str]):
        pagenumber (Union[Unset, int]):
        pagesize (Union[Unset, int]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AlertList
    """

    return (
        await asyncio_detailed(
            client=client,
            include=include,
            filterstatus=filterstatus,
            pagenumber=pagenumber,
            pagesize=pagesize,
        )
    ).parsed
