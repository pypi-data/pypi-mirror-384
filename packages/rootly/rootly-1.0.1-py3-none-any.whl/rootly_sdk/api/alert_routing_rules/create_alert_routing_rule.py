from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.alert_routing_rule_response import AlertRoutingRuleResponse
from ...models.errors_list import ErrorsList
from ...models.new_alert_routing_rule import NewAlertRoutingRule
from ...types import Response


def _get_kwargs(
    *,
    body: NewAlertRoutingRule,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/alert_routing_rules",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/vnd.api+json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[AlertRoutingRuleResponse, ErrorsList]]:
    if response.status_code == 201:
        response_201 = AlertRoutingRuleResponse.from_dict(response.json())

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
) -> Response[Union[AlertRoutingRuleResponse, ErrorsList]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    body: NewAlertRoutingRule,
) -> Response[Union[AlertRoutingRuleResponse, ErrorsList]]:
    """Creates an alert routing rule

     Creates a new alert routing rule from provided data. **Note: If you are an advanced alert routing
    user, you should use the Alert Routes endpoint instead of this endpoint. If you don't know whether
    you are an advanced user, please contact Rootly customer support.**

    Args:
        body (NewAlertRoutingRule):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[AlertRoutingRuleResponse, ErrorsList]]
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
    body: NewAlertRoutingRule,
) -> Optional[Union[AlertRoutingRuleResponse, ErrorsList]]:
    """Creates an alert routing rule

     Creates a new alert routing rule from provided data. **Note: If you are an advanced alert routing
    user, you should use the Alert Routes endpoint instead of this endpoint. If you don't know whether
    you are an advanced user, please contact Rootly customer support.**

    Args:
        body (NewAlertRoutingRule):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[AlertRoutingRuleResponse, ErrorsList]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    body: NewAlertRoutingRule,
) -> Response[Union[AlertRoutingRuleResponse, ErrorsList]]:
    """Creates an alert routing rule

     Creates a new alert routing rule from provided data. **Note: If you are an advanced alert routing
    user, you should use the Alert Routes endpoint instead of this endpoint. If you don't know whether
    you are an advanced user, please contact Rootly customer support.**

    Args:
        body (NewAlertRoutingRule):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[AlertRoutingRuleResponse, ErrorsList]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    body: NewAlertRoutingRule,
) -> Optional[Union[AlertRoutingRuleResponse, ErrorsList]]:
    """Creates an alert routing rule

     Creates a new alert routing rule from provided data. **Note: If you are an advanced alert routing
    user, you should use the Alert Routes endpoint instead of this endpoint. If you don't know whether
    you are an advanced user, please contact Rootly customer support.**

    Args:
        body (NewAlertRoutingRule):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[AlertRoutingRuleResponse, ErrorsList]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
