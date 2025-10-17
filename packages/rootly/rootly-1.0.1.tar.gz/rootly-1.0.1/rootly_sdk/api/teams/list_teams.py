from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.list_teams_include import ListTeamsInclude
from ...models.team_list import TeamList
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    include: Union[Unset, ListTeamsInclude] = UNSET,
    pagenumber: Union[Unset, int] = UNSET,
    pagesize: Union[Unset, int] = UNSET,
    filtersearch: Union[Unset, str] = UNSET,
    filterslug: Union[Unset, str] = UNSET,
    filtername: Union[Unset, str] = UNSET,
    filterbackstage_id: Union[Unset, str] = UNSET,
    filtercortex_id: Union[Unset, str] = UNSET,
    filteropslevel_id: Union[Unset, str] = UNSET,
    filterexternal_id: Union[Unset, str] = UNSET,
    filtercolor: Union[Unset, str] = UNSET,
    filteralert_broadcast_enabled: Union[Unset, bool] = UNSET,
    filterincident_broadcast_enabled: Union[Unset, bool] = UNSET,
    filtercreated_atgt: Union[Unset, str] = UNSET,
    filtercreated_atgte: Union[Unset, str] = UNSET,
    filtercreated_atlt: Union[Unset, str] = UNSET,
    filtercreated_atlte: Union[Unset, str] = UNSET,
    sort: Union[Unset, str] = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    json_include: Union[Unset, str] = UNSET
    if not isinstance(include, Unset):
        json_include = include

    params["include"] = json_include

    params["page[number]"] = pagenumber

    params["page[size]"] = pagesize

    params["filter[search]"] = filtersearch

    params["filter[slug]"] = filterslug

    params["filter[name]"] = filtername

    params["filter[backstage_id]"] = filterbackstage_id

    params["filter[cortex_id]"] = filtercortex_id

    params["filter[opslevel_id]"] = filteropslevel_id

    params["filter[external_id]"] = filterexternal_id

    params["filter[color]"] = filtercolor

    params["filter[alert_broadcast_enabled]"] = filteralert_broadcast_enabled

    params["filter[incident_broadcast_enabled]"] = filterincident_broadcast_enabled

    params["filter[created_at][gt]"] = filtercreated_atgt

    params["filter[created_at][gte]"] = filtercreated_atgte

    params["filter[created_at][lt]"] = filtercreated_atlt

    params["filter[created_at][lte]"] = filtercreated_atlte

    params["sort"] = sort

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v1/teams",
        "params": params,
    }

    return _kwargs


def _parse_response(*, client: Union[AuthenticatedClient, Client], response: httpx.Response) -> Optional[TeamList]:
    if response.status_code == 200:
        response_200 = TeamList.from_dict(response.json())

        return response_200

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(*, client: Union[AuthenticatedClient, Client], response: httpx.Response) -> Response[TeamList]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    include: Union[Unset, ListTeamsInclude] = UNSET,
    pagenumber: Union[Unset, int] = UNSET,
    pagesize: Union[Unset, int] = UNSET,
    filtersearch: Union[Unset, str] = UNSET,
    filterslug: Union[Unset, str] = UNSET,
    filtername: Union[Unset, str] = UNSET,
    filterbackstage_id: Union[Unset, str] = UNSET,
    filtercortex_id: Union[Unset, str] = UNSET,
    filteropslevel_id: Union[Unset, str] = UNSET,
    filterexternal_id: Union[Unset, str] = UNSET,
    filtercolor: Union[Unset, str] = UNSET,
    filteralert_broadcast_enabled: Union[Unset, bool] = UNSET,
    filterincident_broadcast_enabled: Union[Unset, bool] = UNSET,
    filtercreated_atgt: Union[Unset, str] = UNSET,
    filtercreated_atgte: Union[Unset, str] = UNSET,
    filtercreated_atlt: Union[Unset, str] = UNSET,
    filtercreated_atlte: Union[Unset, str] = UNSET,
    sort: Union[Unset, str] = UNSET,
) -> Response[TeamList]:
    """List teams

     List teams

    Args:
        include (Union[Unset, ListTeamsInclude]):
        pagenumber (Union[Unset, int]):
        pagesize (Union[Unset, int]):
        filtersearch (Union[Unset, str]):
        filterslug (Union[Unset, str]):
        filtername (Union[Unset, str]):
        filterbackstage_id (Union[Unset, str]):
        filtercortex_id (Union[Unset, str]):
        filteropslevel_id (Union[Unset, str]):
        filterexternal_id (Union[Unset, str]):
        filtercolor (Union[Unset, str]):
        filteralert_broadcast_enabled (Union[Unset, bool]):
        filterincident_broadcast_enabled (Union[Unset, bool]):
        filtercreated_atgt (Union[Unset, str]):
        filtercreated_atgte (Union[Unset, str]):
        filtercreated_atlt (Union[Unset, str]):
        filtercreated_atlte (Union[Unset, str]):
        sort (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[TeamList]
    """

    kwargs = _get_kwargs(
        include=include,
        pagenumber=pagenumber,
        pagesize=pagesize,
        filtersearch=filtersearch,
        filterslug=filterslug,
        filtername=filtername,
        filterbackstage_id=filterbackstage_id,
        filtercortex_id=filtercortex_id,
        filteropslevel_id=filteropslevel_id,
        filterexternal_id=filterexternal_id,
        filtercolor=filtercolor,
        filteralert_broadcast_enabled=filteralert_broadcast_enabled,
        filterincident_broadcast_enabled=filterincident_broadcast_enabled,
        filtercreated_atgt=filtercreated_atgt,
        filtercreated_atgte=filtercreated_atgte,
        filtercreated_atlt=filtercreated_atlt,
        filtercreated_atlte=filtercreated_atlte,
        sort=sort,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient,
    include: Union[Unset, ListTeamsInclude] = UNSET,
    pagenumber: Union[Unset, int] = UNSET,
    pagesize: Union[Unset, int] = UNSET,
    filtersearch: Union[Unset, str] = UNSET,
    filterslug: Union[Unset, str] = UNSET,
    filtername: Union[Unset, str] = UNSET,
    filterbackstage_id: Union[Unset, str] = UNSET,
    filtercortex_id: Union[Unset, str] = UNSET,
    filteropslevel_id: Union[Unset, str] = UNSET,
    filterexternal_id: Union[Unset, str] = UNSET,
    filtercolor: Union[Unset, str] = UNSET,
    filteralert_broadcast_enabled: Union[Unset, bool] = UNSET,
    filterincident_broadcast_enabled: Union[Unset, bool] = UNSET,
    filtercreated_atgt: Union[Unset, str] = UNSET,
    filtercreated_atgte: Union[Unset, str] = UNSET,
    filtercreated_atlt: Union[Unset, str] = UNSET,
    filtercreated_atlte: Union[Unset, str] = UNSET,
    sort: Union[Unset, str] = UNSET,
) -> Optional[TeamList]:
    """List teams

     List teams

    Args:
        include (Union[Unset, ListTeamsInclude]):
        pagenumber (Union[Unset, int]):
        pagesize (Union[Unset, int]):
        filtersearch (Union[Unset, str]):
        filterslug (Union[Unset, str]):
        filtername (Union[Unset, str]):
        filterbackstage_id (Union[Unset, str]):
        filtercortex_id (Union[Unset, str]):
        filteropslevel_id (Union[Unset, str]):
        filterexternal_id (Union[Unset, str]):
        filtercolor (Union[Unset, str]):
        filteralert_broadcast_enabled (Union[Unset, bool]):
        filterincident_broadcast_enabled (Union[Unset, bool]):
        filtercreated_atgt (Union[Unset, str]):
        filtercreated_atgte (Union[Unset, str]):
        filtercreated_atlt (Union[Unset, str]):
        filtercreated_atlte (Union[Unset, str]):
        sort (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        TeamList
    """

    return sync_detailed(
        client=client,
        include=include,
        pagenumber=pagenumber,
        pagesize=pagesize,
        filtersearch=filtersearch,
        filterslug=filterslug,
        filtername=filtername,
        filterbackstage_id=filterbackstage_id,
        filtercortex_id=filtercortex_id,
        filteropslevel_id=filteropslevel_id,
        filterexternal_id=filterexternal_id,
        filtercolor=filtercolor,
        filteralert_broadcast_enabled=filteralert_broadcast_enabled,
        filterincident_broadcast_enabled=filterincident_broadcast_enabled,
        filtercreated_atgt=filtercreated_atgt,
        filtercreated_atgte=filtercreated_atgte,
        filtercreated_atlt=filtercreated_atlt,
        filtercreated_atlte=filtercreated_atlte,
        sort=sort,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    include: Union[Unset, ListTeamsInclude] = UNSET,
    pagenumber: Union[Unset, int] = UNSET,
    pagesize: Union[Unset, int] = UNSET,
    filtersearch: Union[Unset, str] = UNSET,
    filterslug: Union[Unset, str] = UNSET,
    filtername: Union[Unset, str] = UNSET,
    filterbackstage_id: Union[Unset, str] = UNSET,
    filtercortex_id: Union[Unset, str] = UNSET,
    filteropslevel_id: Union[Unset, str] = UNSET,
    filterexternal_id: Union[Unset, str] = UNSET,
    filtercolor: Union[Unset, str] = UNSET,
    filteralert_broadcast_enabled: Union[Unset, bool] = UNSET,
    filterincident_broadcast_enabled: Union[Unset, bool] = UNSET,
    filtercreated_atgt: Union[Unset, str] = UNSET,
    filtercreated_atgte: Union[Unset, str] = UNSET,
    filtercreated_atlt: Union[Unset, str] = UNSET,
    filtercreated_atlte: Union[Unset, str] = UNSET,
    sort: Union[Unset, str] = UNSET,
) -> Response[TeamList]:
    """List teams

     List teams

    Args:
        include (Union[Unset, ListTeamsInclude]):
        pagenumber (Union[Unset, int]):
        pagesize (Union[Unset, int]):
        filtersearch (Union[Unset, str]):
        filterslug (Union[Unset, str]):
        filtername (Union[Unset, str]):
        filterbackstage_id (Union[Unset, str]):
        filtercortex_id (Union[Unset, str]):
        filteropslevel_id (Union[Unset, str]):
        filterexternal_id (Union[Unset, str]):
        filtercolor (Union[Unset, str]):
        filteralert_broadcast_enabled (Union[Unset, bool]):
        filterincident_broadcast_enabled (Union[Unset, bool]):
        filtercreated_atgt (Union[Unset, str]):
        filtercreated_atgte (Union[Unset, str]):
        filtercreated_atlt (Union[Unset, str]):
        filtercreated_atlte (Union[Unset, str]):
        sort (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[TeamList]
    """

    kwargs = _get_kwargs(
        include=include,
        pagenumber=pagenumber,
        pagesize=pagesize,
        filtersearch=filtersearch,
        filterslug=filterslug,
        filtername=filtername,
        filterbackstage_id=filterbackstage_id,
        filtercortex_id=filtercortex_id,
        filteropslevel_id=filteropslevel_id,
        filterexternal_id=filterexternal_id,
        filtercolor=filtercolor,
        filteralert_broadcast_enabled=filteralert_broadcast_enabled,
        filterincident_broadcast_enabled=filterincident_broadcast_enabled,
        filtercreated_atgt=filtercreated_atgt,
        filtercreated_atgte=filtercreated_atgte,
        filtercreated_atlt=filtercreated_atlt,
        filtercreated_atlte=filtercreated_atlte,
        sort=sort,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    include: Union[Unset, ListTeamsInclude] = UNSET,
    pagenumber: Union[Unset, int] = UNSET,
    pagesize: Union[Unset, int] = UNSET,
    filtersearch: Union[Unset, str] = UNSET,
    filterslug: Union[Unset, str] = UNSET,
    filtername: Union[Unset, str] = UNSET,
    filterbackstage_id: Union[Unset, str] = UNSET,
    filtercortex_id: Union[Unset, str] = UNSET,
    filteropslevel_id: Union[Unset, str] = UNSET,
    filterexternal_id: Union[Unset, str] = UNSET,
    filtercolor: Union[Unset, str] = UNSET,
    filteralert_broadcast_enabled: Union[Unset, bool] = UNSET,
    filterincident_broadcast_enabled: Union[Unset, bool] = UNSET,
    filtercreated_atgt: Union[Unset, str] = UNSET,
    filtercreated_atgte: Union[Unset, str] = UNSET,
    filtercreated_atlt: Union[Unset, str] = UNSET,
    filtercreated_atlte: Union[Unset, str] = UNSET,
    sort: Union[Unset, str] = UNSET,
) -> Optional[TeamList]:
    """List teams

     List teams

    Args:
        include (Union[Unset, ListTeamsInclude]):
        pagenumber (Union[Unset, int]):
        pagesize (Union[Unset, int]):
        filtersearch (Union[Unset, str]):
        filterslug (Union[Unset, str]):
        filtername (Union[Unset, str]):
        filterbackstage_id (Union[Unset, str]):
        filtercortex_id (Union[Unset, str]):
        filteropslevel_id (Union[Unset, str]):
        filterexternal_id (Union[Unset, str]):
        filtercolor (Union[Unset, str]):
        filteralert_broadcast_enabled (Union[Unset, bool]):
        filterincident_broadcast_enabled (Union[Unset, bool]):
        filtercreated_atgt (Union[Unset, str]):
        filtercreated_atgte (Union[Unset, str]):
        filtercreated_atlt (Union[Unset, str]):
        filtercreated_atlte (Union[Unset, str]):
        sort (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        TeamList
    """

    return (
        await asyncio_detailed(
            client=client,
            include=include,
            pagenumber=pagenumber,
            pagesize=pagesize,
            filtersearch=filtersearch,
            filterslug=filterslug,
            filtername=filtername,
            filterbackstage_id=filterbackstage_id,
            filtercortex_id=filtercortex_id,
            filteropslevel_id=filteropslevel_id,
            filterexternal_id=filterexternal_id,
            filtercolor=filtercolor,
            filteralert_broadcast_enabled=filteralert_broadcast_enabled,
            filterincident_broadcast_enabled=filterincident_broadcast_enabled,
            filtercreated_atgt=filtercreated_atgt,
            filtercreated_atgte=filtercreated_atgte,
            filtercreated_atlt=filtercreated_atlt,
            filtercreated_atlte=filtercreated_atlte,
            sort=sort,
        )
    ).parsed
