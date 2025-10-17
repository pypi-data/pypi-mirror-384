from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.communications_stage_response import CommunicationsStageResponse
from ...models.errors_list import ErrorsList
from ...models.update_communications_stage import UpdateCommunicationsStage
from ...types import Response


def _get_kwargs(
    id: str,
    *,
    body: UpdateCommunicationsStage,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "patch",
        "url": f"/v1/communications/stages/{id}",
    }

    _body = body.to_dict()

    _kwargs["json"] = _body
    headers["Content-Type"] = "application/vnd.api+json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[CommunicationsStageResponse, ErrorsList]]:
    if response.status_code == 200:
        response_200 = CommunicationsStageResponse.from_dict(response.json())

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
) -> Response[Union[CommunicationsStageResponse, ErrorsList]]:
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
    body: UpdateCommunicationsStage,
) -> Response[Union[CommunicationsStageResponse, ErrorsList]]:
    """Updates a communications stage

     Updates a communications stage

    Args:
        id (str):
        body (UpdateCommunicationsStage):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[CommunicationsStageResponse, ErrorsList]]
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
    body: UpdateCommunicationsStage,
) -> Optional[Union[CommunicationsStageResponse, ErrorsList]]:
    """Updates a communications stage

     Updates a communications stage

    Args:
        id (str):
        body (UpdateCommunicationsStage):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[CommunicationsStageResponse, ErrorsList]
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
    body: UpdateCommunicationsStage,
) -> Response[Union[CommunicationsStageResponse, ErrorsList]]:
    """Updates a communications stage

     Updates a communications stage

    Args:
        id (str):
        body (UpdateCommunicationsStage):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[CommunicationsStageResponse, ErrorsList]]
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
    body: UpdateCommunicationsStage,
) -> Optional[Union[CommunicationsStageResponse, ErrorsList]]:
    """Updates a communications stage

     Updates a communications stage

    Args:
        id (str):
        body (UpdateCommunicationsStage):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[CommunicationsStageResponse, ErrorsList]
    """

    return (
        await asyncio_detailed(
            id=id,
            client=client,
            body=body,
        )
    ).parsed
