from http import HTTPStatus
from typing import Any, Optional, Union, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.update_a_comment_body import UpdateACommentBody
from ...models.update_a_comment_response_200 import UpdateACommentResponse200
from ...types import Response


def _get_kwargs(
    request_id: str,
    comment_id: str,
    *,
    body: UpdateACommentBody,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "put",
        "url": f"/api/requests/{request_id}/comments/{comment_id}",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[Any, UpdateACommentResponse200]]:
    if response.status_code == 200:
        response_200 = UpdateACommentResponse200.from_dict(response.json())

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
) -> Response[Union[Any, UpdateACommentResponse200]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    request_id: str,
    comment_id: str,
    *,
    client: AuthenticatedClient,
    body: UpdateACommentBody,
) -> Response[Union[Any, UpdateACommentResponse200]]:
    """Update a comment

    Args:
        request_id (str):
        comment_id (str):
        body (UpdateACommentBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, UpdateACommentResponse200]]
    """

    kwargs = _get_kwargs(
        request_id=request_id,
        comment_id=comment_id,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    request_id: str,
    comment_id: str,
    *,
    client: AuthenticatedClient,
    body: UpdateACommentBody,
) -> Optional[Union[Any, UpdateACommentResponse200]]:
    """Update a comment

    Args:
        request_id (str):
        comment_id (str):
        body (UpdateACommentBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, UpdateACommentResponse200]
    """

    return sync_detailed(
        request_id=request_id,
        comment_id=comment_id,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    request_id: str,
    comment_id: str,
    *,
    client: AuthenticatedClient,
    body: UpdateACommentBody,
) -> Response[Union[Any, UpdateACommentResponse200]]:
    """Update a comment

    Args:
        request_id (str):
        comment_id (str):
        body (UpdateACommentBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, UpdateACommentResponse200]]
    """

    kwargs = _get_kwargs(
        request_id=request_id,
        comment_id=comment_id,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    request_id: str,
    comment_id: str,
    *,
    client: AuthenticatedClient,
    body: UpdateACommentBody,
) -> Optional[Union[Any, UpdateACommentResponse200]]:
    """Update a comment

    Args:
        request_id (str):
        comment_id (str):
        body (UpdateACommentBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, UpdateACommentResponse200]
    """

    return (
        await asyncio_detailed(
            request_id=request_id,
            comment_id=comment_id,
            client=client,
            body=body,
        )
    ).parsed
