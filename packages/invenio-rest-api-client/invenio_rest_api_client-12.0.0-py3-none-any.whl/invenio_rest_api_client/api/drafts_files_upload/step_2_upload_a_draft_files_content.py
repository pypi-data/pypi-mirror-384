from http import HTTPStatus
from typing import Any, Optional, Union, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.step_2_upload_a_draft_files_content_response_200 import Step2UploadADraftFilesContentResponse200
from ...types import File, Response


def _get_kwargs(
    draft_id: str,
    file_name: str,
    *,
    body: File,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "put",
        "url": f"/api/records/{draft_id}/draft/files/{file_name}/content",
    }

    _kwargs["content"] = body.payload

    headers["Content-Type"] = "application/octet-stream"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[Any, Step2UploadADraftFilesContentResponse200]]:
    if response.status_code == 200:
        response_200 = Step2UploadADraftFilesContentResponse200.from_dict(response.json())

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
) -> Response[Union[Any, Step2UploadADraftFilesContentResponse200]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    draft_id: str,
    file_name: str,
    *,
    client: AuthenticatedClient,
    body: File,
) -> Response[Union[Any, Step2UploadADraftFilesContentResponse200]]:
    """step[2] Upload a draft file's content

    Args:
        draft_id (str):
        file_name (str):
        body (File):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, Step2UploadADraftFilesContentResponse200]]
    """

    kwargs = _get_kwargs(
        draft_id=draft_id,
        file_name=file_name,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    draft_id: str,
    file_name: str,
    *,
    client: AuthenticatedClient,
    body: File,
) -> Optional[Union[Any, Step2UploadADraftFilesContentResponse200]]:
    """step[2] Upload a draft file's content

    Args:
        draft_id (str):
        file_name (str):
        body (File):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, Step2UploadADraftFilesContentResponse200]
    """

    return sync_detailed(
        draft_id=draft_id,
        file_name=file_name,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    draft_id: str,
    file_name: str,
    *,
    client: AuthenticatedClient,
    body: File,
) -> Response[Union[Any, Step2UploadADraftFilesContentResponse200]]:
    """step[2] Upload a draft file's content

    Args:
        draft_id (str):
        file_name (str):
        body (File):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, Step2UploadADraftFilesContentResponse200]]
    """

    kwargs = _get_kwargs(
        draft_id=draft_id,
        file_name=file_name,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    draft_id: str,
    file_name: str,
    *,
    client: AuthenticatedClient,
    body: File,
) -> Optional[Union[Any, Step2UploadADraftFilesContentResponse200]]:
    """step[2] Upload a draft file's content

    Args:
        draft_id (str):
        file_name (str):
        body (File):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, Step2UploadADraftFilesContentResponse200]
    """

    return (
        await asyncio_detailed(
            draft_id=draft_id,
            file_name=file_name,
            client=client,
            body=body,
        )
    ).parsed
