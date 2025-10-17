from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.alert_urgency_response import AlertUrgencyResponse
from ...models.errors_list import ErrorsList
from ...models.new_alert_urgency import NewAlertUrgency
from ...types import Response


def _get_kwargs(
    *,
    body: NewAlertUrgency,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/alert_urgencies",
    }

    _body = body.to_dict()

    _kwargs["json"] = _body
    headers["Content-Type"] = "application/vnd.api+json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[AlertUrgencyResponse, ErrorsList]]:
    if response.status_code == 201:
        response_201 = AlertUrgencyResponse.from_dict(response.json())

        return response_201
    if response.status_code == 422:
        response_422 = ErrorsList.from_dict(response.json())

        return response_422
    if response.status_code == 401:
        response_401 = ErrorsList.from_dict(response.json())

        return response_401
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[AlertUrgencyResponse, ErrorsList]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    body: NewAlertUrgency,
) -> Response[Union[AlertUrgencyResponse, ErrorsList]]:
    """Creates an alert urgency

     Creates a new alert urgency from provided data

    Args:
        body (NewAlertUrgency):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[AlertUrgencyResponse, ErrorsList]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient,
    body: NewAlertUrgency,
) -> Optional[Union[AlertUrgencyResponse, ErrorsList]]:
    """Creates an alert urgency

     Creates a new alert urgency from provided data

    Args:
        body (NewAlertUrgency):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[AlertUrgencyResponse, ErrorsList]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    body: NewAlertUrgency,
) -> Response[Union[AlertUrgencyResponse, ErrorsList]]:
    """Creates an alert urgency

     Creates a new alert urgency from provided data

    Args:
        body (NewAlertUrgency):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[AlertUrgencyResponse, ErrorsList]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    body: NewAlertUrgency,
) -> Optional[Union[AlertUrgencyResponse, ErrorsList]]:
    """Creates an alert urgency

     Creates a new alert urgency from provided data

    Args:
        body (NewAlertUrgency):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[AlertUrgencyResponse, ErrorsList]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
