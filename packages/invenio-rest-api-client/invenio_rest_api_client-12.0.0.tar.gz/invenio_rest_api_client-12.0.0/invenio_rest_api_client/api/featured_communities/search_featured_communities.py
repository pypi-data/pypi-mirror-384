from http import HTTPStatus
from typing import Any, Optional, Union, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.search_featured_communities_response_200 import SearchFeaturedCommunitiesResponse200
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    prettyprint: Union[Unset, str] = UNSET,
    q: Union[Unset, str] = UNSET,
    size: Union[Unset, str] = UNSET,
    page: Union[Unset, str] = UNSET,
    type_: Union[Unset, str] = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["prettyprint"] = prettyprint

    params["q"] = q

    params["size"] = size

    params["page"] = page

    params["type"] = type_

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/communities/featured",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[Any, SearchFeaturedCommunitiesResponse200]]:
    if response.status_code == 200:
        response_200 = SearchFeaturedCommunitiesResponse200.from_dict(response.json())

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
) -> Response[Union[Any, SearchFeaturedCommunitiesResponse200]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    prettyprint: Union[Unset, str] = UNSET,
    q: Union[Unset, str] = UNSET,
    size: Union[Unset, str] = UNSET,
    page: Union[Unset, str] = UNSET,
    type_: Union[Unset, str] = UNSET,
) -> Response[Union[Any, SearchFeaturedCommunitiesResponse200]]:
    """Search Featured Communities

    Args:
        prettyprint (Union[Unset, str]):
        q (Union[Unset, str]):
        size (Union[Unset, str]):
        page (Union[Unset, str]):
        type_ (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, SearchFeaturedCommunitiesResponse200]]
    """

    kwargs = _get_kwargs(
        prettyprint=prettyprint,
        q=q,
        size=size,
        page=page,
        type_=type_,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient,
    prettyprint: Union[Unset, str] = UNSET,
    q: Union[Unset, str] = UNSET,
    size: Union[Unset, str] = UNSET,
    page: Union[Unset, str] = UNSET,
    type_: Union[Unset, str] = UNSET,
) -> Optional[Union[Any, SearchFeaturedCommunitiesResponse200]]:
    """Search Featured Communities

    Args:
        prettyprint (Union[Unset, str]):
        q (Union[Unset, str]):
        size (Union[Unset, str]):
        page (Union[Unset, str]):
        type_ (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, SearchFeaturedCommunitiesResponse200]
    """

    return sync_detailed(
        client=client,
        prettyprint=prettyprint,
        q=q,
        size=size,
        page=page,
        type_=type_,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    prettyprint: Union[Unset, str] = UNSET,
    q: Union[Unset, str] = UNSET,
    size: Union[Unset, str] = UNSET,
    page: Union[Unset, str] = UNSET,
    type_: Union[Unset, str] = UNSET,
) -> Response[Union[Any, SearchFeaturedCommunitiesResponse200]]:
    """Search Featured Communities

    Args:
        prettyprint (Union[Unset, str]):
        q (Union[Unset, str]):
        size (Union[Unset, str]):
        page (Union[Unset, str]):
        type_ (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, SearchFeaturedCommunitiesResponse200]]
    """

    kwargs = _get_kwargs(
        prettyprint=prettyprint,
        q=q,
        size=size,
        page=page,
        type_=type_,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    prettyprint: Union[Unset, str] = UNSET,
    q: Union[Unset, str] = UNSET,
    size: Union[Unset, str] = UNSET,
    page: Union[Unset, str] = UNSET,
    type_: Union[Unset, str] = UNSET,
) -> Optional[Union[Any, SearchFeaturedCommunitiesResponse200]]:
    """Search Featured Communities

    Args:
        prettyprint (Union[Unset, str]):
        q (Union[Unset, str]):
        size (Union[Unset, str]):
        page (Union[Unset, str]):
        type_ (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, SearchFeaturedCommunitiesResponse200]
    """

    return (
        await asyncio_detailed(
            client=client,
            prettyprint=prettyprint,
            q=q,
            size=size,
            page=page,
            type_=type_,
        )
    ).parsed
