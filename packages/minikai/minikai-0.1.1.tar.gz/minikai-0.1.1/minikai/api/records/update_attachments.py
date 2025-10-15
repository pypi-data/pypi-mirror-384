from http import HTTPStatus
from typing import Any, Optional, Union, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_problem_details import HttpValidationProblemDetails
from ...models.record_attachment import RecordAttachment
from ...models.update_attachments_body import UpdateAttachmentsBody
from ...types import Response


def _get_kwargs(
    record_id: str,
    *,
    body: UpdateAttachmentsBody,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "put",
        "url": f"/api/Records/{record_id}/attachments",
    }

    _kwargs["files"] = body.to_multipart()

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[Any, HttpValidationProblemDetails, list["RecordAttachment"]]]:
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.json()
        for response_200_item_data in _response_200:
            response_200_item = RecordAttachment.from_dict(response_200_item_data)

            response_200.append(response_200_item)

        return response_200

    if response.status_code == 400:
        response_400 = HttpValidationProblemDetails.from_dict(response.json())

        return response_400

    if response.status_code == 404:
        response_404 = cast(Any, None)
        return response_404

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[Any, HttpValidationProblemDetails, list["RecordAttachment"]]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    record_id: str,
    *,
    client: Union[AuthenticatedClient, Client],
    body: UpdateAttachmentsBody,
) -> Response[Union[Any, HttpValidationProblemDetails, list["RecordAttachment"]]]:
    """
    Args:
        record_id (str):
        body (UpdateAttachmentsBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, HttpValidationProblemDetails, list['RecordAttachment']]]
    """

    kwargs = _get_kwargs(
        record_id=record_id,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    record_id: str,
    *,
    client: Union[AuthenticatedClient, Client],
    body: UpdateAttachmentsBody,
) -> Optional[Union[Any, HttpValidationProblemDetails, list["RecordAttachment"]]]:
    """
    Args:
        record_id (str):
        body (UpdateAttachmentsBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, HttpValidationProblemDetails, list['RecordAttachment']]
    """

    return sync_detailed(
        record_id=record_id,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    record_id: str,
    *,
    client: Union[AuthenticatedClient, Client],
    body: UpdateAttachmentsBody,
) -> Response[Union[Any, HttpValidationProblemDetails, list["RecordAttachment"]]]:
    """
    Args:
        record_id (str):
        body (UpdateAttachmentsBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, HttpValidationProblemDetails, list['RecordAttachment']]]
    """

    kwargs = _get_kwargs(
        record_id=record_id,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    record_id: str,
    *,
    client: Union[AuthenticatedClient, Client],
    body: UpdateAttachmentsBody,
) -> Optional[Union[Any, HttpValidationProblemDetails, list["RecordAttachment"]]]:
    """
    Args:
        record_id (str):
        body (UpdateAttachmentsBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, HttpValidationProblemDetails, list['RecordAttachment']]
    """

    return (
        await asyncio_detailed(
            record_id=record_id,
            client=client,
            body=body,
        )
    ).parsed
