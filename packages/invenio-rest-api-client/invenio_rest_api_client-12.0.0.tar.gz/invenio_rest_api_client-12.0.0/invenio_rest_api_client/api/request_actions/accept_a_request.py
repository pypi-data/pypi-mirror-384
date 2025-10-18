from http import HTTPStatus
from typing import Any, Optional, Union, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.accept_a_request_body import AcceptARequestBody
from ...models.created import Created
from ...types import Response


def _get_kwargs(
    request_id: str,
    *,
    body: AcceptARequestBody,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": f"/api/requests/{request_id}/actions/accept",
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
    request_id: str,
    *,
    client: AuthenticatedClient,
    body: AcceptARequestBody,
) -> Response[Union[Any, Created]]:
    """Accept a request

    Args:
        request_id (str):
        body (AcceptARequestBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, Created]]
    """

    kwargs = _get_kwargs(
        request_id=request_id,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    request_id: str,
    *,
    client: AuthenticatedClient,
    body: AcceptARequestBody,
) -> Optional[Union[Any, Created]]:
    """Accept a request

    Args:
        request_id (str):
        body (AcceptARequestBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, Created]
    """

    return sync_detailed(
        request_id=request_id,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    request_id: str,
    *,
    client: AuthenticatedClient,
    body: AcceptARequestBody,
) -> Response[Union[Any, Created]]:
    """Accept a request

    Args:
        request_id (str):
        body (AcceptARequestBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, Created]]
    """

    kwargs = _get_kwargs(
        request_id=request_id,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    request_id: str,
    *,
    client: AuthenticatedClient,
    body: AcceptARequestBody,
) -> Optional[Union[Any, Created]]:
    """Accept a request

    Args:
        request_id (str):
        body (AcceptARequestBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, Created]
    """

    return (
        await asyncio_detailed(
            request_id=request_id,
            client=client,
            body=body,
        )
    ).parsed
