from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.communications_group_response import CommunicationsGroupResponse
from ...models.errors_list import ErrorsList
from ...models.update_communications_group import UpdateCommunicationsGroup
from ...types import Response


def _get_kwargs(
    id: str,
    *,
    body: UpdateCommunicationsGroup,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "patch",
        "url": f"/v1/communications/groups/{id}",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/vnd.api+json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[CommunicationsGroupResponse, ErrorsList]]:
    if response.status_code == 200:
        response_200 = CommunicationsGroupResponse.from_dict(response.json())

        return response_200

    if response.status_code == 422:
        response_422 = ErrorsList.from_dict(response.json())

        return response_422

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[CommunicationsGroupResponse, ErrorsList]]:
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
    body: UpdateCommunicationsGroup,
) -> Response[Union[CommunicationsGroupResponse, ErrorsList]]:
    """Updates a communications group

     Updates a communications group

    Args:
        id (str):
        body (UpdateCommunicationsGroup):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[CommunicationsGroupResponse, ErrorsList]]
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
    body: UpdateCommunicationsGroup,
) -> Optional[Union[CommunicationsGroupResponse, ErrorsList]]:
    """Updates a communications group

     Updates a communications group

    Args:
        id (str):
        body (UpdateCommunicationsGroup):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[CommunicationsGroupResponse, ErrorsList]
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
    body: UpdateCommunicationsGroup,
) -> Response[Union[CommunicationsGroupResponse, ErrorsList]]:
    """Updates a communications group

     Updates a communications group

    Args:
        id (str):
        body (UpdateCommunicationsGroup):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[CommunicationsGroupResponse, ErrorsList]]
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
    body: UpdateCommunicationsGroup,
) -> Optional[Union[CommunicationsGroupResponse, ErrorsList]]:
    """Updates a communications group

     Updates a communications group

    Args:
        id (str):
        body (UpdateCommunicationsGroup):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[CommunicationsGroupResponse, ErrorsList]
    """

    return (
        await asyncio_detailed(
            id=id,
            client=client,
            body=body,
        )
    ).parsed
