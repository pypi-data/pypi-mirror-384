from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.alert_list import AlertList
from ...types import UNSET, Response, Unset


def _get_kwargs(
    incident_id: str,
    *,
    include: Union[Unset, str] = UNSET,
    filtersource: Union[Unset, str] = UNSET,
    filterservices: Union[Unset, str] = UNSET,
    filterenvironments: Union[Unset, str] = UNSET,
    filtergroups: Union[Unset, str] = UNSET,
    filterlabels: Union[Unset, str] = UNSET,
    filterstarted_atgt: Union[Unset, str] = UNSET,
    filterstarted_atgte: Union[Unset, str] = UNSET,
    filterstarted_atlt: Union[Unset, str] = UNSET,
    filterstarted_atlte: Union[Unset, str] = UNSET,
    filterended_atgt: Union[Unset, str] = UNSET,
    filterended_atgte: Union[Unset, str] = UNSET,
    filterended_atlt: Union[Unset, str] = UNSET,
    filterended_atlte: Union[Unset, str] = UNSET,
    filtercreated_atgt: Union[Unset, str] = UNSET,
    filtercreated_atgte: Union[Unset, str] = UNSET,
    filtercreated_atlt: Union[Unset, str] = UNSET,
    filtercreated_atlte: Union[Unset, str] = UNSET,
    pagenumber: Union[Unset, int] = UNSET,
    pagesize: Union[Unset, int] = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["include"] = include

    params["filter[source]"] = filtersource

    params["filter[services]"] = filterservices

    params["filter[environments]"] = filterenvironments

    params["filter[groups]"] = filtergroups

    params["filter[labels]"] = filterlabels

    params["filter[started_at][gt]"] = filterstarted_atgt

    params["filter[started_at][gte]"] = filterstarted_atgte

    params["filter[started_at][lt]"] = filterstarted_atlt

    params["filter[started_at][lte]"] = filterstarted_atlte

    params["filter[ended_at][gt]"] = filterended_atgt

    params["filter[ended_at][gte]"] = filterended_atgte

    params["filter[ended_at][lt]"] = filterended_atlt

    params["filter[ended_at][lte]"] = filterended_atlte

    params["filter[created_at][gt]"] = filtercreated_atgt

    params["filter[created_at][gte]"] = filtercreated_atgte

    params["filter[created_at][lt]"] = filtercreated_atlt

    params["filter[created_at][lte]"] = filtercreated_atlte

    params["page[number]"] = pagenumber

    params["page[size]"] = pagesize

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/v1/incidents/{incident_id}/alerts",
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
    incident_id: str,
    *,
    client: AuthenticatedClient,
    include: Union[Unset, str] = UNSET,
    filtersource: Union[Unset, str] = UNSET,
    filterservices: Union[Unset, str] = UNSET,
    filterenvironments: Union[Unset, str] = UNSET,
    filtergroups: Union[Unset, str] = UNSET,
    filterlabels: Union[Unset, str] = UNSET,
    filterstarted_atgt: Union[Unset, str] = UNSET,
    filterstarted_atgte: Union[Unset, str] = UNSET,
    filterstarted_atlt: Union[Unset, str] = UNSET,
    filterstarted_atlte: Union[Unset, str] = UNSET,
    filterended_atgt: Union[Unset, str] = UNSET,
    filterended_atgte: Union[Unset, str] = UNSET,
    filterended_atlt: Union[Unset, str] = UNSET,
    filterended_atlte: Union[Unset, str] = UNSET,
    filtercreated_atgt: Union[Unset, str] = UNSET,
    filtercreated_atgte: Union[Unset, str] = UNSET,
    filtercreated_atlt: Union[Unset, str] = UNSET,
    filtercreated_atlte: Union[Unset, str] = UNSET,
    pagenumber: Union[Unset, int] = UNSET,
    pagesize: Union[Unset, int] = UNSET,
) -> Response[AlertList]:
    """List Incident alerts

     List incident alerts

    Args:
        incident_id (str):
        include (Union[Unset, str]):
        filtersource (Union[Unset, str]):
        filterservices (Union[Unset, str]):
        filterenvironments (Union[Unset, str]):
        filtergroups (Union[Unset, str]):
        filterlabels (Union[Unset, str]):
        filterstarted_atgt (Union[Unset, str]):
        filterstarted_atgte (Union[Unset, str]):
        filterstarted_atlt (Union[Unset, str]):
        filterstarted_atlte (Union[Unset, str]):
        filterended_atgt (Union[Unset, str]):
        filterended_atgte (Union[Unset, str]):
        filterended_atlt (Union[Unset, str]):
        filterended_atlte (Union[Unset, str]):
        filtercreated_atgt (Union[Unset, str]):
        filtercreated_atgte (Union[Unset, str]):
        filtercreated_atlt (Union[Unset, str]):
        filtercreated_atlte (Union[Unset, str]):
        pagenumber (Union[Unset, int]):
        pagesize (Union[Unset, int]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AlertList]
    """

    kwargs = _get_kwargs(
        incident_id=incident_id,
        include=include,
        filtersource=filtersource,
        filterservices=filterservices,
        filterenvironments=filterenvironments,
        filtergroups=filtergroups,
        filterlabels=filterlabels,
        filterstarted_atgt=filterstarted_atgt,
        filterstarted_atgte=filterstarted_atgte,
        filterstarted_atlt=filterstarted_atlt,
        filterstarted_atlte=filterstarted_atlte,
        filterended_atgt=filterended_atgt,
        filterended_atgte=filterended_atgte,
        filterended_atlt=filterended_atlt,
        filterended_atlte=filterended_atlte,
        filtercreated_atgt=filtercreated_atgt,
        filtercreated_atgte=filtercreated_atgte,
        filtercreated_atlt=filtercreated_atlt,
        filtercreated_atlte=filtercreated_atlte,
        pagenumber=pagenumber,
        pagesize=pagesize,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    incident_id: str,
    *,
    client: AuthenticatedClient,
    include: Union[Unset, str] = UNSET,
    filtersource: Union[Unset, str] = UNSET,
    filterservices: Union[Unset, str] = UNSET,
    filterenvironments: Union[Unset, str] = UNSET,
    filtergroups: Union[Unset, str] = UNSET,
    filterlabels: Union[Unset, str] = UNSET,
    filterstarted_atgt: Union[Unset, str] = UNSET,
    filterstarted_atgte: Union[Unset, str] = UNSET,
    filterstarted_atlt: Union[Unset, str] = UNSET,
    filterstarted_atlte: Union[Unset, str] = UNSET,
    filterended_atgt: Union[Unset, str] = UNSET,
    filterended_atgte: Union[Unset, str] = UNSET,
    filterended_atlt: Union[Unset, str] = UNSET,
    filterended_atlte: Union[Unset, str] = UNSET,
    filtercreated_atgt: Union[Unset, str] = UNSET,
    filtercreated_atgte: Union[Unset, str] = UNSET,
    filtercreated_atlt: Union[Unset, str] = UNSET,
    filtercreated_atlte: Union[Unset, str] = UNSET,
    pagenumber: Union[Unset, int] = UNSET,
    pagesize: Union[Unset, int] = UNSET,
) -> Optional[AlertList]:
    """List Incident alerts

     List incident alerts

    Args:
        incident_id (str):
        include (Union[Unset, str]):
        filtersource (Union[Unset, str]):
        filterservices (Union[Unset, str]):
        filterenvironments (Union[Unset, str]):
        filtergroups (Union[Unset, str]):
        filterlabels (Union[Unset, str]):
        filterstarted_atgt (Union[Unset, str]):
        filterstarted_atgte (Union[Unset, str]):
        filterstarted_atlt (Union[Unset, str]):
        filterstarted_atlte (Union[Unset, str]):
        filterended_atgt (Union[Unset, str]):
        filterended_atgte (Union[Unset, str]):
        filterended_atlt (Union[Unset, str]):
        filterended_atlte (Union[Unset, str]):
        filtercreated_atgt (Union[Unset, str]):
        filtercreated_atgte (Union[Unset, str]):
        filtercreated_atlt (Union[Unset, str]):
        filtercreated_atlte (Union[Unset, str]):
        pagenumber (Union[Unset, int]):
        pagesize (Union[Unset, int]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AlertList
    """

    return sync_detailed(
        incident_id=incident_id,
        client=client,
        include=include,
        filtersource=filtersource,
        filterservices=filterservices,
        filterenvironments=filterenvironments,
        filtergroups=filtergroups,
        filterlabels=filterlabels,
        filterstarted_atgt=filterstarted_atgt,
        filterstarted_atgte=filterstarted_atgte,
        filterstarted_atlt=filterstarted_atlt,
        filterstarted_atlte=filterstarted_atlte,
        filterended_atgt=filterended_atgt,
        filterended_atgte=filterended_atgte,
        filterended_atlt=filterended_atlt,
        filterended_atlte=filterended_atlte,
        filtercreated_atgt=filtercreated_atgt,
        filtercreated_atgte=filtercreated_atgte,
        filtercreated_atlt=filtercreated_atlt,
        filtercreated_atlte=filtercreated_atlte,
        pagenumber=pagenumber,
        pagesize=pagesize,
    ).parsed


async def asyncio_detailed(
    incident_id: str,
    *,
    client: AuthenticatedClient,
    include: Union[Unset, str] = UNSET,
    filtersource: Union[Unset, str] = UNSET,
    filterservices: Union[Unset, str] = UNSET,
    filterenvironments: Union[Unset, str] = UNSET,
    filtergroups: Union[Unset, str] = UNSET,
    filterlabels: Union[Unset, str] = UNSET,
    filterstarted_atgt: Union[Unset, str] = UNSET,
    filterstarted_atgte: Union[Unset, str] = UNSET,
    filterstarted_atlt: Union[Unset, str] = UNSET,
    filterstarted_atlte: Union[Unset, str] = UNSET,
    filterended_atgt: Union[Unset, str] = UNSET,
    filterended_atgte: Union[Unset, str] = UNSET,
    filterended_atlt: Union[Unset, str] = UNSET,
    filterended_atlte: Union[Unset, str] = UNSET,
    filtercreated_atgt: Union[Unset, str] = UNSET,
    filtercreated_atgte: Union[Unset, str] = UNSET,
    filtercreated_atlt: Union[Unset, str] = UNSET,
    filtercreated_atlte: Union[Unset, str] = UNSET,
    pagenumber: Union[Unset, int] = UNSET,
    pagesize: Union[Unset, int] = UNSET,
) -> Response[AlertList]:
    """List Incident alerts

     List incident alerts

    Args:
        incident_id (str):
        include (Union[Unset, str]):
        filtersource (Union[Unset, str]):
        filterservices (Union[Unset, str]):
        filterenvironments (Union[Unset, str]):
        filtergroups (Union[Unset, str]):
        filterlabels (Union[Unset, str]):
        filterstarted_atgt (Union[Unset, str]):
        filterstarted_atgte (Union[Unset, str]):
        filterstarted_atlt (Union[Unset, str]):
        filterstarted_atlte (Union[Unset, str]):
        filterended_atgt (Union[Unset, str]):
        filterended_atgte (Union[Unset, str]):
        filterended_atlt (Union[Unset, str]):
        filterended_atlte (Union[Unset, str]):
        filtercreated_atgt (Union[Unset, str]):
        filtercreated_atgte (Union[Unset, str]):
        filtercreated_atlt (Union[Unset, str]):
        filtercreated_atlte (Union[Unset, str]):
        pagenumber (Union[Unset, int]):
        pagesize (Union[Unset, int]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AlertList]
    """

    kwargs = _get_kwargs(
        incident_id=incident_id,
        include=include,
        filtersource=filtersource,
        filterservices=filterservices,
        filterenvironments=filterenvironments,
        filtergroups=filtergroups,
        filterlabels=filterlabels,
        filterstarted_atgt=filterstarted_atgt,
        filterstarted_atgte=filterstarted_atgte,
        filterstarted_atlt=filterstarted_atlt,
        filterstarted_atlte=filterstarted_atlte,
        filterended_atgt=filterended_atgt,
        filterended_atgte=filterended_atgte,
        filterended_atlt=filterended_atlt,
        filterended_atlte=filterended_atlte,
        filtercreated_atgt=filtercreated_atgt,
        filtercreated_atgte=filtercreated_atgte,
        filtercreated_atlt=filtercreated_atlt,
        filtercreated_atlte=filtercreated_atlte,
        pagenumber=pagenumber,
        pagesize=pagesize,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    incident_id: str,
    *,
    client: AuthenticatedClient,
    include: Union[Unset, str] = UNSET,
    filtersource: Union[Unset, str] = UNSET,
    filterservices: Union[Unset, str] = UNSET,
    filterenvironments: Union[Unset, str] = UNSET,
    filtergroups: Union[Unset, str] = UNSET,
    filterlabels: Union[Unset, str] = UNSET,
    filterstarted_atgt: Union[Unset, str] = UNSET,
    filterstarted_atgte: Union[Unset, str] = UNSET,
    filterstarted_atlt: Union[Unset, str] = UNSET,
    filterstarted_atlte: Union[Unset, str] = UNSET,
    filterended_atgt: Union[Unset, str] = UNSET,
    filterended_atgte: Union[Unset, str] = UNSET,
    filterended_atlt: Union[Unset, str] = UNSET,
    filterended_atlte: Union[Unset, str] = UNSET,
    filtercreated_atgt: Union[Unset, str] = UNSET,
    filtercreated_atgte: Union[Unset, str] = UNSET,
    filtercreated_atlt: Union[Unset, str] = UNSET,
    filtercreated_atlte: Union[Unset, str] = UNSET,
    pagenumber: Union[Unset, int] = UNSET,
    pagesize: Union[Unset, int] = UNSET,
) -> Optional[AlertList]:
    """List Incident alerts

     List incident alerts

    Args:
        incident_id (str):
        include (Union[Unset, str]):
        filtersource (Union[Unset, str]):
        filterservices (Union[Unset, str]):
        filterenvironments (Union[Unset, str]):
        filtergroups (Union[Unset, str]):
        filterlabels (Union[Unset, str]):
        filterstarted_atgt (Union[Unset, str]):
        filterstarted_atgte (Union[Unset, str]):
        filterstarted_atlt (Union[Unset, str]):
        filterstarted_atlte (Union[Unset, str]):
        filterended_atgt (Union[Unset, str]):
        filterended_atgte (Union[Unset, str]):
        filterended_atlt (Union[Unset, str]):
        filterended_atlte (Union[Unset, str]):
        filtercreated_atgt (Union[Unset, str]):
        filtercreated_atgte (Union[Unset, str]):
        filtercreated_atlt (Union[Unset, str]):
        filtercreated_atlte (Union[Unset, str]):
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
            incident_id=incident_id,
            client=client,
            include=include,
            filtersource=filtersource,
            filterservices=filterservices,
            filterenvironments=filterenvironments,
            filtergroups=filtergroups,
            filterlabels=filterlabels,
            filterstarted_atgt=filterstarted_atgt,
            filterstarted_atgte=filterstarted_atgte,
            filterstarted_atlt=filterstarted_atlt,
            filterstarted_atlte=filterstarted_atlte,
            filterended_atgt=filterended_atgt,
            filterended_atgte=filterended_atgte,
            filterended_atlt=filterended_atlt,
            filterended_atlte=filterended_atlte,
            filtercreated_atgt=filtercreated_atgt,
            filtercreated_atgte=filtercreated_atgte,
            filtercreated_atlt=filtercreated_atlt,
            filtercreated_atlte=filtercreated_atlte,
            pagenumber=pagenumber,
            pagesize=pagesize,
        )
    ).parsed
