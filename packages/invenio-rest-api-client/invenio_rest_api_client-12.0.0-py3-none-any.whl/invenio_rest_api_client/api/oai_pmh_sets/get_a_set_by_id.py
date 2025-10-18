from http import HTTPStatus
from typing import Any, Optional, Union, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_a_set_by_id_response_200 import GetASetByIdResponse200
from ...types import Response


def _get_kwargs(
    set_id: str,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/api/oaipmh/sets/{set_id}",
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[Any, GetASetByIdResponse200]]:
    if response.status_code == 200:
        response_200 = GetASetByIdResponse200.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = cast(Any, None)
        return response_400

    if response.status_code == 401:
        response_401 = cast(Any, None)
        return response_401

    if response.status_code == 403:
        response_403 = cast(Any, None)
        return response_403

    if response.status_code == 404:
        response_404 = cast(Any, None)
        return response_404

    if response.status_code == 500:
        response_500 = cast(Any, None)
        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[Any, GetASetByIdResponse200]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    set_id: str,
    *,
    client: AuthenticatedClient,
) -> Response[Union[Any, GetASetByIdResponse200]]:
    """Get a set by ID

    Args:
        set_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, GetASetByIdResponse200]]
    """

    kwargs = _get_kwargs(
        set_id=set_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    set_id: str,
    *,
    client: AuthenticatedClient,
) -> Optional[Union[Any, GetASetByIdResponse200]]:
    """Get a set by ID

    Args:
        set_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, GetASetByIdResponse200]
    """

    return sync_detailed(
        set_id=set_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    set_id: str,
    *,
    client: AuthenticatedClient,
) -> Response[Union[Any, GetASetByIdResponse200]]:
    """Get a set by ID

    Args:
        set_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, GetASetByIdResponse200]]
    """

    kwargs = _get_kwargs(
        set_id=set_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    set_id: str,
    *,
    client: AuthenticatedClient,
) -> Optional[Union[Any, GetASetByIdResponse200]]:
    """Get a set by ID

    Args:
        set_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, GetASetByIdResponse200]
    """

    return (
        await asyncio_detailed(
            set_id=set_id,
            client=client,
        )
    ).parsed
