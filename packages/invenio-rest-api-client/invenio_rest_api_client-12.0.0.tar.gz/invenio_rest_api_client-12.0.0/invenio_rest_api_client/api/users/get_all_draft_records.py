from http import HTTPStatus
from typing import Any, Optional, Union, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_all_draft_records_response_200 import GetAllDraftRecordsResponse200
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    q: Union[Unset, str] = UNSET,
    search: Union[Unset, str] = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["q"] = q

    params["search"] = search

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/user/records",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[Any, GetAllDraftRecordsResponse200]]:
    if response.status_code == 200:
        response_200 = GetAllDraftRecordsResponse200.from_dict(response.json())

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
) -> Response[Union[Any, GetAllDraftRecordsResponse200]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    q: Union[Unset, str] = UNSET,
    search: Union[Unset, str] = UNSET,
) -> Response[Union[Any, GetAllDraftRecordsResponse200]]:
    """Get all draft records

    Args:
        q (Union[Unset, str]):
        search (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, GetAllDraftRecordsResponse200]]
    """

    kwargs = _get_kwargs(
        q=q,
        search=search,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient,
    q: Union[Unset, str] = UNSET,
    search: Union[Unset, str] = UNSET,
) -> Optional[Union[Any, GetAllDraftRecordsResponse200]]:
    """Get all draft records

    Args:
        q (Union[Unset, str]):
        search (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, GetAllDraftRecordsResponse200]
    """

    return sync_detailed(
        client=client,
        q=q,
        search=search,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    q: Union[Unset, str] = UNSET,
    search: Union[Unset, str] = UNSET,
) -> Response[Union[Any, GetAllDraftRecordsResponse200]]:
    """Get all draft records

    Args:
        q (Union[Unset, str]):
        search (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, GetAllDraftRecordsResponse200]]
    """

    kwargs = _get_kwargs(
        q=q,
        search=search,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    q: Union[Unset, str] = UNSET,
    search: Union[Unset, str] = UNSET,
) -> Optional[Union[Any, GetAllDraftRecordsResponse200]]:
    """Get all draft records

    Args:
        q (Union[Unset, str]):
        search (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, GetAllDraftRecordsResponse200]
    """

    return (
        await asyncio_detailed(
            client=client,
            q=q,
            search=search,
        )
    ).parsed
