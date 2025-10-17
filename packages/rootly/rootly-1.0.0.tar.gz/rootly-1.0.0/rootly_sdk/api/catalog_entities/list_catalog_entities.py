from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.catalog_entity_list import CatalogEntityList
from ...models.list_catalog_entities_include import ListCatalogEntitiesInclude
from ...models.list_catalog_entities_sort import ListCatalogEntitiesSort
from ...types import UNSET, Response, Unset


def _get_kwargs(
    catalog_id: str,
    *,
    include: Union[Unset, ListCatalogEntitiesInclude] = UNSET,
    sort: Union[Unset, ListCatalogEntitiesSort] = UNSET,
    pagenumber: Union[Unset, int] = UNSET,
    pagesize: Union[Unset, int] = UNSET,
    filterslug: Union[Unset, str] = UNSET,
    filtername: Union[Unset, str] = UNSET,
    filtercreated_atgt: Union[Unset, str] = UNSET,
    filtercreated_atgte: Union[Unset, str] = UNSET,
    filtercreated_atlt: Union[Unset, str] = UNSET,
    filtercreated_atlte: Union[Unset, str] = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    json_include: Union[Unset, str] = UNSET
    if not isinstance(include, Unset):
        json_include = include.value

    params["include"] = json_include

    json_sort: Union[Unset, str] = UNSET
    if not isinstance(sort, Unset):
        json_sort = sort.value

    params["sort"] = json_sort

    params["page[number]"] = pagenumber

    params["page[size]"] = pagesize

    params["filter[slug]"] = filterslug

    params["filter[name]"] = filtername

    params["filter[created_at][gt]"] = filtercreated_atgt

    params["filter[created_at][gte]"] = filtercreated_atgte

    params["filter[created_at][lt]"] = filtercreated_atlt

    params["filter[created_at][lte]"] = filtercreated_atlte

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/v1/catalogs/{catalog_id}/entities",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[CatalogEntityList]:
    if response.status_code == 200:
        response_200 = CatalogEntityList.from_dict(response.json())

        return response_200
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[CatalogEntityList]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    catalog_id: str,
    *,
    client: AuthenticatedClient,
    include: Union[Unset, ListCatalogEntitiesInclude] = UNSET,
    sort: Union[Unset, ListCatalogEntitiesSort] = UNSET,
    pagenumber: Union[Unset, int] = UNSET,
    pagesize: Union[Unset, int] = UNSET,
    filterslug: Union[Unset, str] = UNSET,
    filtername: Union[Unset, str] = UNSET,
    filtercreated_atgt: Union[Unset, str] = UNSET,
    filtercreated_atgte: Union[Unset, str] = UNSET,
    filtercreated_atlt: Union[Unset, str] = UNSET,
    filtercreated_atlte: Union[Unset, str] = UNSET,
) -> Response[CatalogEntityList]:
    """List Catalog Entities

     List Catalog Entities

    Args:
        catalog_id (str):
        include (Union[Unset, ListCatalogEntitiesInclude]):
        sort (Union[Unset, ListCatalogEntitiesSort]):
        pagenumber (Union[Unset, int]):
        pagesize (Union[Unset, int]):
        filterslug (Union[Unset, str]):
        filtername (Union[Unset, str]):
        filtercreated_atgt (Union[Unset, str]):
        filtercreated_atgte (Union[Unset, str]):
        filtercreated_atlt (Union[Unset, str]):
        filtercreated_atlte (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CatalogEntityList]
    """

    kwargs = _get_kwargs(
        catalog_id=catalog_id,
        include=include,
        sort=sort,
        pagenumber=pagenumber,
        pagesize=pagesize,
        filterslug=filterslug,
        filtername=filtername,
        filtercreated_atgt=filtercreated_atgt,
        filtercreated_atgte=filtercreated_atgte,
        filtercreated_atlt=filtercreated_atlt,
        filtercreated_atlte=filtercreated_atlte,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    catalog_id: str,
    *,
    client: AuthenticatedClient,
    include: Union[Unset, ListCatalogEntitiesInclude] = UNSET,
    sort: Union[Unset, ListCatalogEntitiesSort] = UNSET,
    pagenumber: Union[Unset, int] = UNSET,
    pagesize: Union[Unset, int] = UNSET,
    filterslug: Union[Unset, str] = UNSET,
    filtername: Union[Unset, str] = UNSET,
    filtercreated_atgt: Union[Unset, str] = UNSET,
    filtercreated_atgte: Union[Unset, str] = UNSET,
    filtercreated_atlt: Union[Unset, str] = UNSET,
    filtercreated_atlte: Union[Unset, str] = UNSET,
) -> Optional[CatalogEntityList]:
    """List Catalog Entities

     List Catalog Entities

    Args:
        catalog_id (str):
        include (Union[Unset, ListCatalogEntitiesInclude]):
        sort (Union[Unset, ListCatalogEntitiesSort]):
        pagenumber (Union[Unset, int]):
        pagesize (Union[Unset, int]):
        filterslug (Union[Unset, str]):
        filtername (Union[Unset, str]):
        filtercreated_atgt (Union[Unset, str]):
        filtercreated_atgte (Union[Unset, str]):
        filtercreated_atlt (Union[Unset, str]):
        filtercreated_atlte (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CatalogEntityList
    """

    return sync_detailed(
        catalog_id=catalog_id,
        client=client,
        include=include,
        sort=sort,
        pagenumber=pagenumber,
        pagesize=pagesize,
        filterslug=filterslug,
        filtername=filtername,
        filtercreated_atgt=filtercreated_atgt,
        filtercreated_atgte=filtercreated_atgte,
        filtercreated_atlt=filtercreated_atlt,
        filtercreated_atlte=filtercreated_atlte,
    ).parsed


async def asyncio_detailed(
    catalog_id: str,
    *,
    client: AuthenticatedClient,
    include: Union[Unset, ListCatalogEntitiesInclude] = UNSET,
    sort: Union[Unset, ListCatalogEntitiesSort] = UNSET,
    pagenumber: Union[Unset, int] = UNSET,
    pagesize: Union[Unset, int] = UNSET,
    filterslug: Union[Unset, str] = UNSET,
    filtername: Union[Unset, str] = UNSET,
    filtercreated_atgt: Union[Unset, str] = UNSET,
    filtercreated_atgte: Union[Unset, str] = UNSET,
    filtercreated_atlt: Union[Unset, str] = UNSET,
    filtercreated_atlte: Union[Unset, str] = UNSET,
) -> Response[CatalogEntityList]:
    """List Catalog Entities

     List Catalog Entities

    Args:
        catalog_id (str):
        include (Union[Unset, ListCatalogEntitiesInclude]):
        sort (Union[Unset, ListCatalogEntitiesSort]):
        pagenumber (Union[Unset, int]):
        pagesize (Union[Unset, int]):
        filterslug (Union[Unset, str]):
        filtername (Union[Unset, str]):
        filtercreated_atgt (Union[Unset, str]):
        filtercreated_atgte (Union[Unset, str]):
        filtercreated_atlt (Union[Unset, str]):
        filtercreated_atlte (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CatalogEntityList]
    """

    kwargs = _get_kwargs(
        catalog_id=catalog_id,
        include=include,
        sort=sort,
        pagenumber=pagenumber,
        pagesize=pagesize,
        filterslug=filterslug,
        filtername=filtername,
        filtercreated_atgt=filtercreated_atgt,
        filtercreated_atgte=filtercreated_atgte,
        filtercreated_atlt=filtercreated_atlt,
        filtercreated_atlte=filtercreated_atlte,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    catalog_id: str,
    *,
    client: AuthenticatedClient,
    include: Union[Unset, ListCatalogEntitiesInclude] = UNSET,
    sort: Union[Unset, ListCatalogEntitiesSort] = UNSET,
    pagenumber: Union[Unset, int] = UNSET,
    pagesize: Union[Unset, int] = UNSET,
    filterslug: Union[Unset, str] = UNSET,
    filtername: Union[Unset, str] = UNSET,
    filtercreated_atgt: Union[Unset, str] = UNSET,
    filtercreated_atgte: Union[Unset, str] = UNSET,
    filtercreated_atlt: Union[Unset, str] = UNSET,
    filtercreated_atlte: Union[Unset, str] = UNSET,
) -> Optional[CatalogEntityList]:
    """List Catalog Entities

     List Catalog Entities

    Args:
        catalog_id (str):
        include (Union[Unset, ListCatalogEntitiesInclude]):
        sort (Union[Unset, ListCatalogEntitiesSort]):
        pagenumber (Union[Unset, int]):
        pagesize (Union[Unset, int]):
        filterslug (Union[Unset, str]):
        filtername (Union[Unset, str]):
        filtercreated_atgt (Union[Unset, str]):
        filtercreated_atgte (Union[Unset, str]):
        filtercreated_atlt (Union[Unset, str]):
        filtercreated_atlte (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CatalogEntityList
    """

    return (
        await asyncio_detailed(
            catalog_id=catalog_id,
            client=client,
            include=include,
            sort=sort,
            pagenumber=pagenumber,
            pagesize=pagesize,
            filterslug=filterslug,
            filtername=filtername,
            filtercreated_atgt=filtercreated_atgt,
            filtercreated_atgte=filtercreated_atgte,
            filtercreated_atlt=filtercreated_atlt,
            filtercreated_atlte=filtercreated_atlte,
        )
    ).parsed
