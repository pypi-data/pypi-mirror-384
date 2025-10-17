from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.errors_list import ErrorsList
from ...models.incident_custom_field_selection_response import IncidentCustomFieldSelectionResponse
from ...models.update_incident_custom_field_selection import UpdateIncidentCustomFieldSelection
from ...types import Response


def _get_kwargs(
    id: str,
    *,
    body: UpdateIncidentCustomFieldSelection,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "put",
        "url": f"/v1/incident_custom_field_selections/{id}",
    }

    _body = body.to_dict()

    _kwargs["json"] = _body
    headers["Content-Type"] = "application/vnd.api+json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[ErrorsList, IncidentCustomFieldSelectionResponse]]:
    if response.status_code == 200:
        response_200 = IncidentCustomFieldSelectionResponse.from_dict(response.json())

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
) -> Response[Union[ErrorsList, IncidentCustomFieldSelectionResponse]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    id: str,
    *,
    client: AuthenticatedClient,
    body: UpdateIncidentCustomFieldSelection,
) -> Response[Union[ErrorsList, IncidentCustomFieldSelectionResponse]]:
    """[DEPRECATED] Update an incident custom field selection

     [DEPRECATED] Use form field endpoints instead. Update a specific incident custom field selection by
    id

    Args:
        id (str):
        body (UpdateIncidentCustomFieldSelection):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ErrorsList, IncidentCustomFieldSelectionResponse]]
    """

    kwargs = _get_kwargs(
        id=id,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    id: str,
    *,
    client: AuthenticatedClient,
    body: UpdateIncidentCustomFieldSelection,
) -> Optional[Union[ErrorsList, IncidentCustomFieldSelectionResponse]]:
    """[DEPRECATED] Update an incident custom field selection

     [DEPRECATED] Use form field endpoints instead. Update a specific incident custom field selection by
    id

    Args:
        id (str):
        body (UpdateIncidentCustomFieldSelection):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ErrorsList, IncidentCustomFieldSelectionResponse]
    """

    return sync_detailed(
        id=id,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    id: str,
    *,
    client: AuthenticatedClient,
    body: UpdateIncidentCustomFieldSelection,
) -> Response[Union[ErrorsList, IncidentCustomFieldSelectionResponse]]:
    """[DEPRECATED] Update an incident custom field selection

     [DEPRECATED] Use form field endpoints instead. Update a specific incident custom field selection by
    id

    Args:
        id (str):
        body (UpdateIncidentCustomFieldSelection):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ErrorsList, IncidentCustomFieldSelectionResponse]]
    """

    kwargs = _get_kwargs(
        id=id,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    id: str,
    *,
    client: AuthenticatedClient,
    body: UpdateIncidentCustomFieldSelection,
) -> Optional[Union[ErrorsList, IncidentCustomFieldSelectionResponse]]:
    """[DEPRECATED] Update an incident custom field selection

     [DEPRECATED] Use form field endpoints instead. Update a specific incident custom field selection by
    id

    Args:
        id (str):
        body (UpdateIncidentCustomFieldSelection):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ErrorsList, IncidentCustomFieldSelectionResponse]
    """

    return (
        await asyncio_detailed(
            id=id,
            client=client,
            body=body,
        )
    ).parsed
