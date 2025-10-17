from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.errors_list import ErrorsList
from ...models.incident_action_item_response import IncidentActionItemResponse
from ...models.new_incident_action_item import NewIncidentActionItem
from ...types import Response


def _get_kwargs(
    incident_id: str,
    *,
    body: NewIncidentActionItem,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": f"/v1/incidents/{incident_id}/action_items",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/vnd.api+json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[ErrorsList, IncidentActionItemResponse]]:
    if response.status_code == 201:
        response_201 = IncidentActionItemResponse.from_dict(response.json())

        return response_201

    if response.status_code == 401:
        response_401 = ErrorsList.from_dict(response.json())

        return response_401

    if response.status_code == 422:
        response_422 = ErrorsList.from_dict(response.json())

        return response_422

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[ErrorsList, IncidentActionItemResponse]]:
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
    body: NewIncidentActionItem,
) -> Response[Union[ErrorsList, IncidentActionItemResponse]]:
    """Creates an incident action item

     Creates a new action item from provided data

    Args:
        incident_id (str):
        body (NewIncidentActionItem):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ErrorsList, IncidentActionItemResponse]]
    """

    kwargs = _get_kwargs(
        incident_id=incident_id,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    incident_id: str,
    *,
    client: AuthenticatedClient,
    body: NewIncidentActionItem,
) -> Optional[Union[ErrorsList, IncidentActionItemResponse]]:
    """Creates an incident action item

     Creates a new action item from provided data

    Args:
        incident_id (str):
        body (NewIncidentActionItem):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ErrorsList, IncidentActionItemResponse]
    """

    return sync_detailed(
        incident_id=incident_id,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    incident_id: str,
    *,
    client: AuthenticatedClient,
    body: NewIncidentActionItem,
) -> Response[Union[ErrorsList, IncidentActionItemResponse]]:
    """Creates an incident action item

     Creates a new action item from provided data

    Args:
        incident_id (str):
        body (NewIncidentActionItem):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ErrorsList, IncidentActionItemResponse]]
    """

    kwargs = _get_kwargs(
        incident_id=incident_id,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    incident_id: str,
    *,
    client: AuthenticatedClient,
    body: NewIncidentActionItem,
) -> Optional[Union[ErrorsList, IncidentActionItemResponse]]:
    """Creates an incident action item

     Creates a new action item from provided data

    Args:
        incident_id (str):
        body (NewIncidentActionItem):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ErrorsList, IncidentActionItemResponse]
    """

    return (
        await asyncio_detailed(
            incident_id=incident_id,
            client=client,
            body=body,
        )
    ).parsed
