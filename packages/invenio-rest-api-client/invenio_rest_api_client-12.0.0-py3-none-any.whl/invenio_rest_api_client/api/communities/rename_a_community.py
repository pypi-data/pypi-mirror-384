from http import HTTPStatus
from typing import Any, Optional, Union, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.created import Created
from ...models.rename_a_community_body import RenameACommunityBody
from ...types import Response


def _get_kwargs(
    community_id: str,
    *,
    body: RenameACommunityBody,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": f"/api/communities/{community_id}/rename",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[Any, Created]]:
    if response.status_code == 201:
        response_201 = Created.from_dict(response.json())

        return response_201

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
) -> Response[Union[Any, Created]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    community_id: str,
    *,
    client: AuthenticatedClient,
    body: RenameACommunityBody,
) -> Response[Union[Any, Created]]:
    """Rename a Community

    Args:
        community_id (str):
        body (RenameACommunityBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, Created]]
    """

    kwargs = _get_kwargs(
        community_id=community_id,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    community_id: str,
    *,
    client: AuthenticatedClient,
    body: RenameACommunityBody,
) -> Optional[Union[Any, Created]]:
    """Rename a Community

    Args:
        community_id (str):
        body (RenameACommunityBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, Created]
    """

    return sync_detailed(
        community_id=community_id,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    community_id: str,
    *,
    client: AuthenticatedClient,
    body: RenameACommunityBody,
) -> Response[Union[Any, Created]]:
    """Rename a Community

    Args:
        community_id (str):
        body (RenameACommunityBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, Created]]
    """

    kwargs = _get_kwargs(
        community_id=community_id,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    community_id: str,
    *,
    client: AuthenticatedClient,
    body: RenameACommunityBody,
) -> Optional[Union[Any, Created]]:
    """Rename a Community

    Args:
        community_id (str):
        body (RenameACommunityBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, Created]
    """

    return (
        await asyncio_detailed(
            community_id=community_id,
            client=client,
            body=body,
        )
    ).parsed
