from http import HTTPStatus
from typing import Any, Optional, Union, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.search_vocabularies_response_200 import SearchVocabulariesResponse200
from ...types import UNSET, Response, Unset


def _get_kwargs(
    vocabularies_type: str,
    *,
    q: Union[Unset, str] = UNSET,
    suggest: Union[Unset, str] = UNSET,
    tags: Union[Unset, str] = UNSET,
    sort: Union[Unset, str] = UNSET,
    size: Union[Unset, str] = UNSET,
    page: Union[Unset, str] = UNSET,
    ln: Union[Unset, str] = UNSET,
    accept_language: Union[Unset, str] = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["q"] = q

    params["suggest"] = suggest

    params["tags"] = tags

    params["sort"] = sort

    params["size"] = size

    params["page"] = page

    params["ln"] = ln

    params["accept-language"] = accept_language

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/api/vocabularies/{vocabularies_type}",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[Any, SearchVocabulariesResponse200]]:
    if response.status_code == 200:
        response_200 = SearchVocabulariesResponse200.from_dict(response.json())

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
) -> Response[Union[Any, SearchVocabulariesResponse200]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    vocabularies_type: str,
    *,
    client: AuthenticatedClient,
    q: Union[Unset, str] = UNSET,
    suggest: Union[Unset, str] = UNSET,
    tags: Union[Unset, str] = UNSET,
    sort: Union[Unset, str] = UNSET,
    size: Union[Unset, str] = UNSET,
    page: Union[Unset, str] = UNSET,
    ln: Union[Unset, str] = UNSET,
    accept_language: Union[Unset, str] = UNSET,
) -> Response[Union[Any, SearchVocabulariesResponse200]]:
    """Search vocabularies

    Args:
        vocabularies_type (str):
        q (Union[Unset, str]):
        suggest (Union[Unset, str]):
        tags (Union[Unset, str]):
        sort (Union[Unset, str]):
        size (Union[Unset, str]):
        page (Union[Unset, str]):
        ln (Union[Unset, str]):
        accept_language (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, SearchVocabulariesResponse200]]
    """

    kwargs = _get_kwargs(
        vocabularies_type=vocabularies_type,
        q=q,
        suggest=suggest,
        tags=tags,
        sort=sort,
        size=size,
        page=page,
        ln=ln,
        accept_language=accept_language,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    vocabularies_type: str,
    *,
    client: AuthenticatedClient,
    q: Union[Unset, str] = UNSET,
    suggest: Union[Unset, str] = UNSET,
    tags: Union[Unset, str] = UNSET,
    sort: Union[Unset, str] = UNSET,
    size: Union[Unset, str] = UNSET,
    page: Union[Unset, str] = UNSET,
    ln: Union[Unset, str] = UNSET,
    accept_language: Union[Unset, str] = UNSET,
) -> Optional[Union[Any, SearchVocabulariesResponse200]]:
    """Search vocabularies

    Args:
        vocabularies_type (str):
        q (Union[Unset, str]):
        suggest (Union[Unset, str]):
        tags (Union[Unset, str]):
        sort (Union[Unset, str]):
        size (Union[Unset, str]):
        page (Union[Unset, str]):
        ln (Union[Unset, str]):
        accept_language (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, SearchVocabulariesResponse200]
    """

    return sync_detailed(
        vocabularies_type=vocabularies_type,
        client=client,
        q=q,
        suggest=suggest,
        tags=tags,
        sort=sort,
        size=size,
        page=page,
        ln=ln,
        accept_language=accept_language,
    ).parsed


async def asyncio_detailed(
    vocabularies_type: str,
    *,
    client: AuthenticatedClient,
    q: Union[Unset, str] = UNSET,
    suggest: Union[Unset, str] = UNSET,
    tags: Union[Unset, str] = UNSET,
    sort: Union[Unset, str] = UNSET,
    size: Union[Unset, str] = UNSET,
    page: Union[Unset, str] = UNSET,
    ln: Union[Unset, str] = UNSET,
    accept_language: Union[Unset, str] = UNSET,
) -> Response[Union[Any, SearchVocabulariesResponse200]]:
    """Search vocabularies

    Args:
        vocabularies_type (str):
        q (Union[Unset, str]):
        suggest (Union[Unset, str]):
        tags (Union[Unset, str]):
        sort (Union[Unset, str]):
        size (Union[Unset, str]):
        page (Union[Unset, str]):
        ln (Union[Unset, str]):
        accept_language (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, SearchVocabulariesResponse200]]
    """

    kwargs = _get_kwargs(
        vocabularies_type=vocabularies_type,
        q=q,
        suggest=suggest,
        tags=tags,
        sort=sort,
        size=size,
        page=page,
        ln=ln,
        accept_language=accept_language,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    vocabularies_type: str,
    *,
    client: AuthenticatedClient,
    q: Union[Unset, str] = UNSET,
    suggest: Union[Unset, str] = UNSET,
    tags: Union[Unset, str] = UNSET,
    sort: Union[Unset, str] = UNSET,
    size: Union[Unset, str] = UNSET,
    page: Union[Unset, str] = UNSET,
    ln: Union[Unset, str] = UNSET,
    accept_language: Union[Unset, str] = UNSET,
) -> Optional[Union[Any, SearchVocabulariesResponse200]]:
    """Search vocabularies

    Args:
        vocabularies_type (str):
        q (Union[Unset, str]):
        suggest (Union[Unset, str]):
        tags (Union[Unset, str]):
        sort (Union[Unset, str]):
        size (Union[Unset, str]):
        page (Union[Unset, str]):
        ln (Union[Unset, str]):
        accept_language (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, SearchVocabulariesResponse200]
    """

    return (
        await asyncio_detailed(
            vocabularies_type=vocabularies_type,
            client=client,
            q=q,
            suggest=suggest,
            tags=tags,
            sort=sort,
            size=size,
            page=page,
            ln=ln,
            accept_language=accept_language,
        )
    ).parsed
