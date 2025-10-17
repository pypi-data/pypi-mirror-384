from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.incident_post_mortem_list import IncidentPostMortemList
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    include: Union[Unset, str] = UNSET,
    pagenumber: Union[Unset, int] = UNSET,
    pagesize: Union[Unset, int] = UNSET,
    filtersearch: Union[Unset, str] = UNSET,
    filterstatus: Union[Unset, str] = UNSET,
    filterseverity: Union[Unset, str] = UNSET,
    filtertype: Union[Unset, str] = UNSET,
    filteruser_id: Union[Unset, int] = UNSET,
    filterenvironments: Union[Unset, str] = UNSET,
    filterfunctionalities: Union[Unset, str] = UNSET,
    filterservices: Union[Unset, str] = UNSET,
    filterteams: Union[Unset, str] = UNSET,
    filtercreated_atgt: Union[Unset, str] = UNSET,
    filtercreated_atgte: Union[Unset, str] = UNSET,
    filtercreated_atlt: Union[Unset, str] = UNSET,
    filtercreated_atlte: Union[Unset, str] = UNSET,
    filterstarted_atgt: Union[Unset, str] = UNSET,
    filterstarted_atgte: Union[Unset, str] = UNSET,
    filterstarted_atlt: Union[Unset, str] = UNSET,
    filterstarted_atlte: Union[Unset, str] = UNSET,
    filtermitigated_atgt: Union[Unset, str] = UNSET,
    filtermitigated_atgte: Union[Unset, str] = UNSET,
    filtermitigated_atlt: Union[Unset, str] = UNSET,
    filtermitigated_atlte: Union[Unset, str] = UNSET,
    filterresolved_atgt: Union[Unset, str] = UNSET,
    filterresolved_atgte: Union[Unset, str] = UNSET,
    filterresolved_atlt: Union[Unset, str] = UNSET,
    filterresolved_atlte: Union[Unset, str] = UNSET,
    sort: Union[Unset, str] = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["include"] = include

    params["page[number]"] = pagenumber

    params["page[size]"] = pagesize

    params["filter[search]"] = filtersearch

    params["filter[status]"] = filterstatus

    params["filter[severity]"] = filterseverity

    params["filter[type]"] = filtertype

    params["filter[user_id]"] = filteruser_id

    params["filter[environments]"] = filterenvironments

    params["filter[functionalities]"] = filterfunctionalities

    params["filter[services]"] = filterservices

    params["filter[teams]"] = filterteams

    params["filter[created_at][gt]"] = filtercreated_atgt

    params["filter[created_at][gte]"] = filtercreated_atgte

    params["filter[created_at][lt]"] = filtercreated_atlt

    params["filter[created_at][lte]"] = filtercreated_atlte

    params["filter[started_at][gt]"] = filterstarted_atgt

    params["filter[started_at][gte]"] = filterstarted_atgte

    params["filter[started_at][lt]"] = filterstarted_atlt

    params["filter[started_at][lte]"] = filterstarted_atlte

    params["filter[mitigated_at][gt]"] = filtermitigated_atgt

    params["filter[mitigated_at][gte]"] = filtermitigated_atgte

    params["filter[mitigated_at][lt]"] = filtermitigated_atlt

    params["filter[mitigated_at][lte]"] = filtermitigated_atlte

    params["filter[resolved_at][gt]"] = filterresolved_atgt

    params["filter[resolved_at][gte]"] = filterresolved_atgte

    params["filter[resolved_at][lt]"] = filterresolved_atlt

    params["filter[resolved_at][lte]"] = filterresolved_atlte

    params["sort"] = sort

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v1/post_mortems",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[IncidentPostMortemList]:
    if response.status_code == 200:
        response_200 = IncidentPostMortemList.from_dict(response.json())

        return response_200
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[IncidentPostMortemList]:
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
    pagenumber: Union[Unset, int] = UNSET,
    pagesize: Union[Unset, int] = UNSET,
    filtersearch: Union[Unset, str] = UNSET,
    filterstatus: Union[Unset, str] = UNSET,
    filterseverity: Union[Unset, str] = UNSET,
    filtertype: Union[Unset, str] = UNSET,
    filteruser_id: Union[Unset, int] = UNSET,
    filterenvironments: Union[Unset, str] = UNSET,
    filterfunctionalities: Union[Unset, str] = UNSET,
    filterservices: Union[Unset, str] = UNSET,
    filterteams: Union[Unset, str] = UNSET,
    filtercreated_atgt: Union[Unset, str] = UNSET,
    filtercreated_atgte: Union[Unset, str] = UNSET,
    filtercreated_atlt: Union[Unset, str] = UNSET,
    filtercreated_atlte: Union[Unset, str] = UNSET,
    filterstarted_atgt: Union[Unset, str] = UNSET,
    filterstarted_atgte: Union[Unset, str] = UNSET,
    filterstarted_atlt: Union[Unset, str] = UNSET,
    filterstarted_atlte: Union[Unset, str] = UNSET,
    filtermitigated_atgt: Union[Unset, str] = UNSET,
    filtermitigated_atgte: Union[Unset, str] = UNSET,
    filtermitigated_atlt: Union[Unset, str] = UNSET,
    filtermitigated_atlte: Union[Unset, str] = UNSET,
    filterresolved_atgt: Union[Unset, str] = UNSET,
    filterresolved_atgte: Union[Unset, str] = UNSET,
    filterresolved_atlt: Union[Unset, str] = UNSET,
    filterresolved_atlte: Union[Unset, str] = UNSET,
    sort: Union[Unset, str] = UNSET,
) -> Response[IncidentPostMortemList]:
    """List incident retrospectives

     List incident retrospectives

    Args:
        include (Union[Unset, str]):
        pagenumber (Union[Unset, int]):
        pagesize (Union[Unset, int]):
        filtersearch (Union[Unset, str]):
        filterstatus (Union[Unset, str]):
        filterseverity (Union[Unset, str]):
        filtertype (Union[Unset, str]):
        filteruser_id (Union[Unset, int]):
        filterenvironments (Union[Unset, str]):
        filterfunctionalities (Union[Unset, str]):
        filterservices (Union[Unset, str]):
        filterteams (Union[Unset, str]):
        filtercreated_atgt (Union[Unset, str]):
        filtercreated_atgte (Union[Unset, str]):
        filtercreated_atlt (Union[Unset, str]):
        filtercreated_atlte (Union[Unset, str]):
        filterstarted_atgt (Union[Unset, str]):
        filterstarted_atgte (Union[Unset, str]):
        filterstarted_atlt (Union[Unset, str]):
        filterstarted_atlte (Union[Unset, str]):
        filtermitigated_atgt (Union[Unset, str]):
        filtermitigated_atgte (Union[Unset, str]):
        filtermitigated_atlt (Union[Unset, str]):
        filtermitigated_atlte (Union[Unset, str]):
        filterresolved_atgt (Union[Unset, str]):
        filterresolved_atgte (Union[Unset, str]):
        filterresolved_atlt (Union[Unset, str]):
        filterresolved_atlte (Union[Unset, str]):
        sort (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[IncidentPostMortemList]
    """

    kwargs = _get_kwargs(
        include=include,
        pagenumber=pagenumber,
        pagesize=pagesize,
        filtersearch=filtersearch,
        filterstatus=filterstatus,
        filterseverity=filterseverity,
        filtertype=filtertype,
        filteruser_id=filteruser_id,
        filterenvironments=filterenvironments,
        filterfunctionalities=filterfunctionalities,
        filterservices=filterservices,
        filterteams=filterteams,
        filtercreated_atgt=filtercreated_atgt,
        filtercreated_atgte=filtercreated_atgte,
        filtercreated_atlt=filtercreated_atlt,
        filtercreated_atlte=filtercreated_atlte,
        filterstarted_atgt=filterstarted_atgt,
        filterstarted_atgte=filterstarted_atgte,
        filterstarted_atlt=filterstarted_atlt,
        filterstarted_atlte=filterstarted_atlte,
        filtermitigated_atgt=filtermitigated_atgt,
        filtermitigated_atgte=filtermitigated_atgte,
        filtermitigated_atlt=filtermitigated_atlt,
        filtermitigated_atlte=filtermitigated_atlte,
        filterresolved_atgt=filterresolved_atgt,
        filterresolved_atgte=filterresolved_atgte,
        filterresolved_atlt=filterresolved_atlt,
        filterresolved_atlte=filterresolved_atlte,
        sort=sort,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient,
    include: Union[Unset, str] = UNSET,
    pagenumber: Union[Unset, int] = UNSET,
    pagesize: Union[Unset, int] = UNSET,
    filtersearch: Union[Unset, str] = UNSET,
    filterstatus: Union[Unset, str] = UNSET,
    filterseverity: Union[Unset, str] = UNSET,
    filtertype: Union[Unset, str] = UNSET,
    filteruser_id: Union[Unset, int] = UNSET,
    filterenvironments: Union[Unset, str] = UNSET,
    filterfunctionalities: Union[Unset, str] = UNSET,
    filterservices: Union[Unset, str] = UNSET,
    filterteams: Union[Unset, str] = UNSET,
    filtercreated_atgt: Union[Unset, str] = UNSET,
    filtercreated_atgte: Union[Unset, str] = UNSET,
    filtercreated_atlt: Union[Unset, str] = UNSET,
    filtercreated_atlte: Union[Unset, str] = UNSET,
    filterstarted_atgt: Union[Unset, str] = UNSET,
    filterstarted_atgte: Union[Unset, str] = UNSET,
    filterstarted_atlt: Union[Unset, str] = UNSET,
    filterstarted_atlte: Union[Unset, str] = UNSET,
    filtermitigated_atgt: Union[Unset, str] = UNSET,
    filtermitigated_atgte: Union[Unset, str] = UNSET,
    filtermitigated_atlt: Union[Unset, str] = UNSET,
    filtermitigated_atlte: Union[Unset, str] = UNSET,
    filterresolved_atgt: Union[Unset, str] = UNSET,
    filterresolved_atgte: Union[Unset, str] = UNSET,
    filterresolved_atlt: Union[Unset, str] = UNSET,
    filterresolved_atlte: Union[Unset, str] = UNSET,
    sort: Union[Unset, str] = UNSET,
) -> Optional[IncidentPostMortemList]:
    """List incident retrospectives

     List incident retrospectives

    Args:
        include (Union[Unset, str]):
        pagenumber (Union[Unset, int]):
        pagesize (Union[Unset, int]):
        filtersearch (Union[Unset, str]):
        filterstatus (Union[Unset, str]):
        filterseverity (Union[Unset, str]):
        filtertype (Union[Unset, str]):
        filteruser_id (Union[Unset, int]):
        filterenvironments (Union[Unset, str]):
        filterfunctionalities (Union[Unset, str]):
        filterservices (Union[Unset, str]):
        filterteams (Union[Unset, str]):
        filtercreated_atgt (Union[Unset, str]):
        filtercreated_atgte (Union[Unset, str]):
        filtercreated_atlt (Union[Unset, str]):
        filtercreated_atlte (Union[Unset, str]):
        filterstarted_atgt (Union[Unset, str]):
        filterstarted_atgte (Union[Unset, str]):
        filterstarted_atlt (Union[Unset, str]):
        filterstarted_atlte (Union[Unset, str]):
        filtermitigated_atgt (Union[Unset, str]):
        filtermitigated_atgte (Union[Unset, str]):
        filtermitigated_atlt (Union[Unset, str]):
        filtermitigated_atlte (Union[Unset, str]):
        filterresolved_atgt (Union[Unset, str]):
        filterresolved_atgte (Union[Unset, str]):
        filterresolved_atlt (Union[Unset, str]):
        filterresolved_atlte (Union[Unset, str]):
        sort (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        IncidentPostMortemList
    """

    return sync_detailed(
        client=client,
        include=include,
        pagenumber=pagenumber,
        pagesize=pagesize,
        filtersearch=filtersearch,
        filterstatus=filterstatus,
        filterseverity=filterseverity,
        filtertype=filtertype,
        filteruser_id=filteruser_id,
        filterenvironments=filterenvironments,
        filterfunctionalities=filterfunctionalities,
        filterservices=filterservices,
        filterteams=filterteams,
        filtercreated_atgt=filtercreated_atgt,
        filtercreated_atgte=filtercreated_atgte,
        filtercreated_atlt=filtercreated_atlt,
        filtercreated_atlte=filtercreated_atlte,
        filterstarted_atgt=filterstarted_atgt,
        filterstarted_atgte=filterstarted_atgte,
        filterstarted_atlt=filterstarted_atlt,
        filterstarted_atlte=filterstarted_atlte,
        filtermitigated_atgt=filtermitigated_atgt,
        filtermitigated_atgte=filtermitigated_atgte,
        filtermitigated_atlt=filtermitigated_atlt,
        filtermitigated_atlte=filtermitigated_atlte,
        filterresolved_atgt=filterresolved_atgt,
        filterresolved_atgte=filterresolved_atgte,
        filterresolved_atlt=filterresolved_atlt,
        filterresolved_atlte=filterresolved_atlte,
        sort=sort,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    include: Union[Unset, str] = UNSET,
    pagenumber: Union[Unset, int] = UNSET,
    pagesize: Union[Unset, int] = UNSET,
    filtersearch: Union[Unset, str] = UNSET,
    filterstatus: Union[Unset, str] = UNSET,
    filterseverity: Union[Unset, str] = UNSET,
    filtertype: Union[Unset, str] = UNSET,
    filteruser_id: Union[Unset, int] = UNSET,
    filterenvironments: Union[Unset, str] = UNSET,
    filterfunctionalities: Union[Unset, str] = UNSET,
    filterservices: Union[Unset, str] = UNSET,
    filterteams: Union[Unset, str] = UNSET,
    filtercreated_atgt: Union[Unset, str] = UNSET,
    filtercreated_atgte: Union[Unset, str] = UNSET,
    filtercreated_atlt: Union[Unset, str] = UNSET,
    filtercreated_atlte: Union[Unset, str] = UNSET,
    filterstarted_atgt: Union[Unset, str] = UNSET,
    filterstarted_atgte: Union[Unset, str] = UNSET,
    filterstarted_atlt: Union[Unset, str] = UNSET,
    filterstarted_atlte: Union[Unset, str] = UNSET,
    filtermitigated_atgt: Union[Unset, str] = UNSET,
    filtermitigated_atgte: Union[Unset, str] = UNSET,
    filtermitigated_atlt: Union[Unset, str] = UNSET,
    filtermitigated_atlte: Union[Unset, str] = UNSET,
    filterresolved_atgt: Union[Unset, str] = UNSET,
    filterresolved_atgte: Union[Unset, str] = UNSET,
    filterresolved_atlt: Union[Unset, str] = UNSET,
    filterresolved_atlte: Union[Unset, str] = UNSET,
    sort: Union[Unset, str] = UNSET,
) -> Response[IncidentPostMortemList]:
    """List incident retrospectives

     List incident retrospectives

    Args:
        include (Union[Unset, str]):
        pagenumber (Union[Unset, int]):
        pagesize (Union[Unset, int]):
        filtersearch (Union[Unset, str]):
        filterstatus (Union[Unset, str]):
        filterseverity (Union[Unset, str]):
        filtertype (Union[Unset, str]):
        filteruser_id (Union[Unset, int]):
        filterenvironments (Union[Unset, str]):
        filterfunctionalities (Union[Unset, str]):
        filterservices (Union[Unset, str]):
        filterteams (Union[Unset, str]):
        filtercreated_atgt (Union[Unset, str]):
        filtercreated_atgte (Union[Unset, str]):
        filtercreated_atlt (Union[Unset, str]):
        filtercreated_atlte (Union[Unset, str]):
        filterstarted_atgt (Union[Unset, str]):
        filterstarted_atgte (Union[Unset, str]):
        filterstarted_atlt (Union[Unset, str]):
        filterstarted_atlte (Union[Unset, str]):
        filtermitigated_atgt (Union[Unset, str]):
        filtermitigated_atgte (Union[Unset, str]):
        filtermitigated_atlt (Union[Unset, str]):
        filtermitigated_atlte (Union[Unset, str]):
        filterresolved_atgt (Union[Unset, str]):
        filterresolved_atgte (Union[Unset, str]):
        filterresolved_atlt (Union[Unset, str]):
        filterresolved_atlte (Union[Unset, str]):
        sort (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[IncidentPostMortemList]
    """

    kwargs = _get_kwargs(
        include=include,
        pagenumber=pagenumber,
        pagesize=pagesize,
        filtersearch=filtersearch,
        filterstatus=filterstatus,
        filterseverity=filterseverity,
        filtertype=filtertype,
        filteruser_id=filteruser_id,
        filterenvironments=filterenvironments,
        filterfunctionalities=filterfunctionalities,
        filterservices=filterservices,
        filterteams=filterteams,
        filtercreated_atgt=filtercreated_atgt,
        filtercreated_atgte=filtercreated_atgte,
        filtercreated_atlt=filtercreated_atlt,
        filtercreated_atlte=filtercreated_atlte,
        filterstarted_atgt=filterstarted_atgt,
        filterstarted_atgte=filterstarted_atgte,
        filterstarted_atlt=filterstarted_atlt,
        filterstarted_atlte=filterstarted_atlte,
        filtermitigated_atgt=filtermitigated_atgt,
        filtermitigated_atgte=filtermitigated_atgte,
        filtermitigated_atlt=filtermitigated_atlt,
        filtermitigated_atlte=filtermitigated_atlte,
        filterresolved_atgt=filterresolved_atgt,
        filterresolved_atgte=filterresolved_atgte,
        filterresolved_atlt=filterresolved_atlt,
        filterresolved_atlte=filterresolved_atlte,
        sort=sort,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    include: Union[Unset, str] = UNSET,
    pagenumber: Union[Unset, int] = UNSET,
    pagesize: Union[Unset, int] = UNSET,
    filtersearch: Union[Unset, str] = UNSET,
    filterstatus: Union[Unset, str] = UNSET,
    filterseverity: Union[Unset, str] = UNSET,
    filtertype: Union[Unset, str] = UNSET,
    filteruser_id: Union[Unset, int] = UNSET,
    filterenvironments: Union[Unset, str] = UNSET,
    filterfunctionalities: Union[Unset, str] = UNSET,
    filterservices: Union[Unset, str] = UNSET,
    filterteams: Union[Unset, str] = UNSET,
    filtercreated_atgt: Union[Unset, str] = UNSET,
    filtercreated_atgte: Union[Unset, str] = UNSET,
    filtercreated_atlt: Union[Unset, str] = UNSET,
    filtercreated_atlte: Union[Unset, str] = UNSET,
    filterstarted_atgt: Union[Unset, str] = UNSET,
    filterstarted_atgte: Union[Unset, str] = UNSET,
    filterstarted_atlt: Union[Unset, str] = UNSET,
    filterstarted_atlte: Union[Unset, str] = UNSET,
    filtermitigated_atgt: Union[Unset, str] = UNSET,
    filtermitigated_atgte: Union[Unset, str] = UNSET,
    filtermitigated_atlt: Union[Unset, str] = UNSET,
    filtermitigated_atlte: Union[Unset, str] = UNSET,
    filterresolved_atgt: Union[Unset, str] = UNSET,
    filterresolved_atgte: Union[Unset, str] = UNSET,
    filterresolved_atlt: Union[Unset, str] = UNSET,
    filterresolved_atlte: Union[Unset, str] = UNSET,
    sort: Union[Unset, str] = UNSET,
) -> Optional[IncidentPostMortemList]:
    """List incident retrospectives

     List incident retrospectives

    Args:
        include (Union[Unset, str]):
        pagenumber (Union[Unset, int]):
        pagesize (Union[Unset, int]):
        filtersearch (Union[Unset, str]):
        filterstatus (Union[Unset, str]):
        filterseverity (Union[Unset, str]):
        filtertype (Union[Unset, str]):
        filteruser_id (Union[Unset, int]):
        filterenvironments (Union[Unset, str]):
        filterfunctionalities (Union[Unset, str]):
        filterservices (Union[Unset, str]):
        filterteams (Union[Unset, str]):
        filtercreated_atgt (Union[Unset, str]):
        filtercreated_atgte (Union[Unset, str]):
        filtercreated_atlt (Union[Unset, str]):
        filtercreated_atlte (Union[Unset, str]):
        filterstarted_atgt (Union[Unset, str]):
        filterstarted_atgte (Union[Unset, str]):
        filterstarted_atlt (Union[Unset, str]):
        filterstarted_atlte (Union[Unset, str]):
        filtermitigated_atgt (Union[Unset, str]):
        filtermitigated_atgte (Union[Unset, str]):
        filtermitigated_atlt (Union[Unset, str]):
        filtermitigated_atlte (Union[Unset, str]):
        filterresolved_atgt (Union[Unset, str]):
        filterresolved_atgte (Union[Unset, str]):
        filterresolved_atlt (Union[Unset, str]):
        filterresolved_atlte (Union[Unset, str]):
        sort (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        IncidentPostMortemList
    """

    return (
        await asyncio_detailed(
            client=client,
            include=include,
            pagenumber=pagenumber,
            pagesize=pagesize,
            filtersearch=filtersearch,
            filterstatus=filterstatus,
            filterseverity=filterseverity,
            filtertype=filtertype,
            filteruser_id=filteruser_id,
            filterenvironments=filterenvironments,
            filterfunctionalities=filterfunctionalities,
            filterservices=filterservices,
            filterteams=filterteams,
            filtercreated_atgt=filtercreated_atgt,
            filtercreated_atgte=filtercreated_atgte,
            filtercreated_atlt=filtercreated_atlt,
            filtercreated_atlte=filtercreated_atlte,
            filterstarted_atgt=filterstarted_atgt,
            filterstarted_atgte=filterstarted_atgte,
            filterstarted_atlt=filterstarted_atlt,
            filterstarted_atlte=filterstarted_atlte,
            filtermitigated_atgt=filtermitigated_atgt,
            filtermitigated_atgte=filtermitigated_atgte,
            filtermitigated_atlt=filtermitigated_atlt,
            filtermitigated_atlte=filtermitigated_atlte,
            filterresolved_atgt=filterresolved_atgt,
            filterresolved_atgte=filterresolved_atgte,
            filterresolved_atlt=filterresolved_atlt,
            filterresolved_atlte=filterresolved_atlte,
            sort=sort,
        )
    ).parsed
