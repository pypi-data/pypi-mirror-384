from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.error import Error
from ...models.request_token import RequestToken
from ...models.request_token_response import RequestTokenResponse
from ...types import Response


def _get_kwargs(
    realm: str,
    *,
    body: RequestToken,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": f"/realms/{realm}/protocol/openid-connect/token",
    }

    _kwargs["data"] = body.to_dict()

    headers["Content-Type"] = "application/x-www-form-urlencoded"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[Error, RequestTokenResponse]]:
    if response.status_code == 200:
        response_200 = RequestTokenResponse.from_dict(response.json())

        return response_200

    if response.status_code == 401:
        response_401 = Error.from_dict(response.json())

        return response_401

    if response.status_code == 404:
        response_404 = Error.from_dict(response.json())

        return response_404

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[Error, RequestTokenResponse]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    realm: str,
    *,
    client: Union[AuthenticatedClient, Client],
    body: RequestToken,
) -> Response[Union[Error, RequestTokenResponse]]:
    """Request Token.

     Using the `/token` endpoint, poll for a token with the new device code grant type.

    The link with the previous step is done with the `device_code` returned previously:

    Args:
        realm (str):
        body (RequestToken):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, RequestTokenResponse]]
    """

    kwargs = _get_kwargs(
        realm=realm,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    realm: str,
    *,
    client: Union[AuthenticatedClient, Client],
    body: RequestToken,
) -> Optional[Union[Error, RequestTokenResponse]]:
    """Request Token.

     Using the `/token` endpoint, poll for a token with the new device code grant type.

    The link with the previous step is done with the `device_code` returned previously:

    Args:
        realm (str):
        body (RequestToken):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, RequestTokenResponse]
    """

    return sync_detailed(
        realm=realm,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    realm: str,
    *,
    client: Union[AuthenticatedClient, Client],
    body: RequestToken,
) -> Response[Union[Error, RequestTokenResponse]]:
    """Request Token.

     Using the `/token` endpoint, poll for a token with the new device code grant type.

    The link with the previous step is done with the `device_code` returned previously:

    Args:
        realm (str):
        body (RequestToken):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, RequestTokenResponse]]
    """

    kwargs = _get_kwargs(
        realm=realm,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    realm: str,
    *,
    client: Union[AuthenticatedClient, Client],
    body: RequestToken,
) -> Optional[Union[Error, RequestTokenResponse]]:
    """Request Token.

     Using the `/token` endpoint, poll for a token with the new device code grant type.

    The link with the previous step is done with the `device_code` returned previously:

    Args:
        realm (str):
        body (RequestToken):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, RequestTokenResponse]
    """

    return (
        await asyncio_detailed(
            realm=realm,
            client=client,
            body=body,
        )
    ).parsed
