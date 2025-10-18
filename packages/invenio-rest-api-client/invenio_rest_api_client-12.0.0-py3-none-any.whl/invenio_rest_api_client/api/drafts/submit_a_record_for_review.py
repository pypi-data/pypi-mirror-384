from http import HTTPStatus
from typing import Any, Optional, Union, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.created import Created
from ...models.submit_a_record_for_review_body import SubmitARecordForReviewBody
from ...types import Response


def _get_kwargs(
    draft_id: str,
    *,
    body: SubmitARecordForReviewBody,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": f"/api/records/{draft_id}/draft/actions/submit-review",
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
    draft_id: str,
    *,
    client: AuthenticatedClient,
    body: SubmitARecordForReviewBody,
) -> Response[Union[Any, Created]]:
    """Submit a record for review

    Args:
        draft_id (str):
        body (SubmitARecordForReviewBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, Created]]
    """

    kwargs = _get_kwargs(
        draft_id=draft_id,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    draft_id: str,
    *,
    client: AuthenticatedClient,
    body: SubmitARecordForReviewBody,
) -> Optional[Union[Any, Created]]:
    """Submit a record for review

    Args:
        draft_id (str):
        body (SubmitARecordForReviewBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, Created]
    """

    return sync_detailed(
        draft_id=draft_id,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    draft_id: str,
    *,
    client: AuthenticatedClient,
    body: SubmitARecordForReviewBody,
) -> Response[Union[Any, Created]]:
    """Submit a record for review

    Args:
        draft_id (str):
        body (SubmitARecordForReviewBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, Created]]
    """

    kwargs = _get_kwargs(
        draft_id=draft_id,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    draft_id: str,
    *,
    client: AuthenticatedClient,
    body: SubmitARecordForReviewBody,
) -> Optional[Union[Any, Created]]:
    """Submit a record for review

    Args:
        draft_id (str):
        body (SubmitARecordForReviewBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, Created]
    """

    return (
        await asyncio_detailed(
            draft_id=draft_id,
            client=client,
            body=body,
        )
    ).parsed
