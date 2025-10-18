from http import HTTPStatus
from typing import Any, Optional, Union, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.error import Error
from ...types import UNSET, Response, Unset


def _get_kwargs(
    room_id: str,
    id: str,
    *,
    peer_id: Union[Unset, str] = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["peer_id"] = peer_id

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/room/{room_id}/peer/{id}/subscribe_peer".format(
            room_id=room_id,
            id=id,
        ),
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[Any, Error]]:
    if response.status_code == 200:
        response_200 = cast(Any, None)
        return response_200
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
) -> Response[Union[Any, Error]]:
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
    peer_id: Union[Unset, str] = UNSET,
) -> Response[Union[Any, Error]]:
    """Subscribe peer to another peer's tracks

    Args:
        room_id (str):
        id (str):
        peer_id (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, Error]]
    """

    kwargs = _get_kwargs(
        room_id=room_id,
        id=id,
        peer_id=peer_id,
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
    peer_id: Union[Unset, str] = UNSET,
) -> Optional[Union[Any, Error]]:
    """Subscribe peer to another peer's tracks

    Args:
        room_id (str):
        id (str):
        peer_id (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, Error]
    """

    return sync_detailed(
        room_id=room_id,
        id=id,
        client=client,
        peer_id=peer_id,
    ).parsed


async def asyncio_detailed(
    room_id: str,
    id: str,
    *,
    client: AuthenticatedClient,
    peer_id: Union[Unset, str] = UNSET,
) -> Response[Union[Any, Error]]:
    """Subscribe peer to another peer's tracks

    Args:
        room_id (str):
        id (str):
        peer_id (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, Error]]
    """

    kwargs = _get_kwargs(
        room_id=room_id,
        id=id,
        peer_id=peer_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    room_id: str,
    id: str,
    *,
    client: AuthenticatedClient,
    peer_id: Union[Unset, str] = UNSET,
) -> Optional[Union[Any, Error]]:
    """Subscribe peer to another peer's tracks

    Args:
        room_id (str):
        id (str):
        peer_id (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, Error]
    """

    return (
        await asyncio_detailed(
            room_id=room_id,
            id=id,
            client=client,
            peer_id=peer_id,
        )
    ).parsed
