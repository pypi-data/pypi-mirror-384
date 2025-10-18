from http import HTTPStatus
from typing import Any, Optional, Union, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.update_a_draft_record_response_200 import UpdateADraftRecordResponse200
from ...models.update_draft_record import UpdateDraftRecord
from ...types import Response


def _get_kwargs(
    draft_id: str,
    *,
    body: UpdateDraftRecord,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "put",
        "url": f"/api/records/{draft_id}/draft",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[Any, UpdateADraftRecordResponse200]]:
    if response.status_code == 200:
        response_200 = UpdateADraftRecordResponse200.from_dict(response.json())

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
) -> Response[Union[Any, UpdateADraftRecordResponse200]]:
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
    body: UpdateDraftRecord,
) -> Response[Union[Any, UpdateADraftRecordResponse200]]:
    """Update a draft record

    Args:
        draft_id (str):
        body (UpdateDraftRecord):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, UpdateADraftRecordResponse200]]
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
    body: UpdateDraftRecord,
) -> Optional[Union[Any, UpdateADraftRecordResponse200]]:
    """Update a draft record

    Args:
        draft_id (str):
        body (UpdateDraftRecord):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, UpdateADraftRecordResponse200]
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
    body: UpdateDraftRecord,
) -> Response[Union[Any, UpdateADraftRecordResponse200]]:
    """Update a draft record

    Args:
        draft_id (str):
        body (UpdateDraftRecord):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, UpdateADraftRecordResponse200]]
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
    body: UpdateDraftRecord,
) -> Optional[Union[Any, UpdateADraftRecordResponse200]]:
    """Update a draft record

    Args:
        draft_id (str):
        body (UpdateDraftRecord):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, UpdateADraftRecordResponse200]
    """

    return (
        await asyncio_detailed(
            draft_id=draft_id,
            client=client,
            body=body,
        )
    ).parsed
