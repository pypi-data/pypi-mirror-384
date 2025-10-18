from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.error import Error
from ...models.peer_refresh_token_response import PeerRefreshTokenResponse
from ...types import Response


def _get_kwargs(
    room_id: str,
    id: str,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/room/{room_id}/peer/{id}/refresh_token".format(
            room_id=room_id,
            id=id,
        ),
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[Error, PeerRefreshTokenResponse]]:
    if response.status_code == 201:
        response_201 = PeerRefreshTokenResponse.from_dict(response.json())

        return response_201
    if response.status_code == 400:
        response_400 = Error.from_dict(response.json())

        return response_400
    if response.status_code == 401:
        response_401 = Error.from_dict(response.json())

        return response_401
    if response.status_code == 404:
        response_404 = Error.from_dict(response.json())

        return response_404
    if response.status_code == 503:
        response_503 = Error.from_dict(response.json())

        return response_503
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[Error, PeerRefreshTokenResponse]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    room_id: str,
    id: str,
    *,
    client: AuthenticatedClient,
) -> Response[Union[Error, PeerRefreshTokenResponse]]:
    """Refresh peer token

    Args:
        room_id (str):
        id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, PeerRefreshTokenResponse]]
    """

    kwargs = _get_kwargs(
        room_id=room_id,
        id=id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    room_id: str,
    id: str,
    *,
    client: AuthenticatedClient,
) -> Optional[Union[Error, PeerRefreshTokenResponse]]:
    """Refresh peer token

    Args:
        room_id (str):
        id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, PeerRefreshTokenResponse]
    """

    return sync_detailed(
        room_id=room_id,
        id=id,
        client=client,
    ).parsed


async def asyncio_detailed(
    room_id: str,
    id: str,
    *,
    client: AuthenticatedClient,
) -> Response[Union[Error, PeerRefreshTokenResponse]]:
    """Refresh peer token

    Args:
        room_id (str):
        id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, PeerRefreshTokenResponse]]
    """

    kwargs = _get_kwargs(
        room_id=room_id,
        id=id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    room_id: str,
    id: str,
    *,
    client: AuthenticatedClient,
) -> Optional[Union[Error, PeerRefreshTokenResponse]]:
    """Refresh peer token

    Args:
        room_id (str):
        id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, PeerRefreshTokenResponse]
    """

    return (
        await asyncio_detailed(
            room_id=room_id,
            id=id,
            client=client,
        )
    ).parsed
