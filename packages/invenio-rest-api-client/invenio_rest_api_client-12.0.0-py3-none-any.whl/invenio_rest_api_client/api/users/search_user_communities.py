from http import HTTPStatus
from typing import Any, Optional, Union, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.search_user_communities_response_200 import SearchUserCommunitiesResponse200
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    page: Union[Unset, str] = UNSET,
    type_: Union[Unset, str] = UNSET,
    size: Union[Unset, str] = UNSET,
    sort: Union[Unset, str] = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["page"] = page

    params["type"] = type_

    params["size"] = size

    params["sort"] = sort

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/user/communities",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[Any, SearchUserCommunitiesResponse200]]:
    if response.status_code == 200:
        response_200 = SearchUserCommunitiesResponse200.from_dict(response.json())

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
) -> Response[Union[Any, SearchUserCommunitiesResponse200]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    page: Union[Unset, str] = UNSET,
    type_: Union[Unset, str] = UNSET,
    size: Union[Unset, str] = UNSET,
    sort: Union[Unset, str] = UNSET,
) -> Response[Union[Any, SearchUserCommunitiesResponse200]]:
    """Search User Communities

    Args:
        page (Union[Unset, str]):
        type_ (Union[Unset, str]):
        size (Union[Unset, str]):
        sort (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, SearchUserCommunitiesResponse200]]
    """

    kwargs = _get_kwargs(
        page=page,
        type_=type_,
        size=size,
        sort=sort,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient,
    page: Union[Unset, str] = UNSET,
    type_: Union[Unset, str] = UNSET,
    size: Union[Unset, str] = UNSET,
    sort: Union[Unset, str] = UNSET,
) -> Optional[Union[Any, SearchUserCommunitiesResponse200]]:
    """Search User Communities

    Args:
        page (Union[Unset, str]):
        type_ (Union[Unset, str]):
        size (Union[Unset, str]):
        sort (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, SearchUserCommunitiesResponse200]
    """

    return sync_detailed(
        client=client,
        page=page,
        type_=type_,
        size=size,
        sort=sort,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    page: Union[Unset, str] = UNSET,
    type_: Union[Unset, str] = UNSET,
    size: Union[Unset, str] = UNSET,
    sort: Union[Unset, str] = UNSET,
) -> Response[Union[Any, SearchUserCommunitiesResponse200]]:
    """Search User Communities

    Args:
        page (Union[Unset, str]):
        type_ (Union[Unset, str]):
        size (Union[Unset, str]):
        sort (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, SearchUserCommunitiesResponse200]]
    """

    kwargs = _get_kwargs(
        page=page,
        type_=type_,
        size=size,
        sort=sort,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    page: Union[Unset, str] = UNSET,
    type_: Union[Unset, str] = UNSET,
    size: Union[Unset, str] = UNSET,
    sort: Union[Unset, str] = UNSET,
) -> Optional[Union[Any, SearchUserCommunitiesResponse200]]:
    """Search User Communities

    Args:
        page (Union[Unset, str]):
        type_ (Union[Unset, str]):
        size (Union[Unset, str]):
        sort (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, SearchUserCommunitiesResponse200]
    """

    return (
        await asyncio_detailed(
            client=client,
            page=page,
            type_=type_,
            size=size,
            sort=sort,
        )
    ).parsed
