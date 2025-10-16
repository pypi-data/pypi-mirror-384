from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.paginated_list_of_record_dto import PaginatedListOfRecordDto
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    body: list[str],
    mini_id: Union[None, Unset, str] = UNSET,
    session_id: Union[None, Unset, str] = UNSET,
    page_number: Union[Unset, int] = 1,
    page_size: Union[Unset, int] = 10,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    params: dict[str, Any] = {}

    json_mini_id: Union[None, Unset, str]
    if isinstance(mini_id, Unset):
        json_mini_id = UNSET
    else:
        json_mini_id = mini_id
    params["miniId"] = json_mini_id

    json_session_id: Union[None, Unset, str]
    if isinstance(session_id, Unset):
        json_session_id = UNSET
    else:
        json_session_id = session_id
    params["sessionId"] = json_session_id

    params["pageNumber"] = page_number

    params["pageSize"] = page_size

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/Records/external",
        "params": params,
    }

    _kwargs["json"] = body

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[PaginatedListOfRecordDto]:
    if response.status_code == 200:
        response_200 = PaginatedListOfRecordDto.from_dict(response.json())

        return response_200

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[PaginatedListOfRecordDto]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: list[str],
    mini_id: Union[None, Unset, str] = UNSET,
    session_id: Union[None, Unset, str] = UNSET,
    page_number: Union[Unset, int] = 1,
    page_size: Union[Unset, int] = 10,
) -> Response[PaginatedListOfRecordDto]:
    """
    Args:
        mini_id (Union[None, Unset, str]):
        session_id (Union[None, Unset, str]):
        page_number (Union[Unset, int]):  Default: 1.
        page_size (Union[Unset, int]):  Default: 10.
        body (list[str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PaginatedListOfRecordDto]
    """

    kwargs = _get_kwargs(
        body=body,
        mini_id=mini_id,
        session_id=session_id,
        page_number=page_number,
        page_size=page_size,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    body: list[str],
    mini_id: Union[None, Unset, str] = UNSET,
    session_id: Union[None, Unset, str] = UNSET,
    page_number: Union[Unset, int] = 1,
    page_size: Union[Unset, int] = 10,
) -> Optional[PaginatedListOfRecordDto]:
    """
    Args:
        mini_id (Union[None, Unset, str]):
        session_id (Union[None, Unset, str]):
        page_number (Union[Unset, int]):  Default: 1.
        page_size (Union[Unset, int]):  Default: 10.
        body (list[str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PaginatedListOfRecordDto
    """

    return sync_detailed(
        client=client,
        body=body,
        mini_id=mini_id,
        session_id=session_id,
        page_number=page_number,
        page_size=page_size,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: list[str],
    mini_id: Union[None, Unset, str] = UNSET,
    session_id: Union[None, Unset, str] = UNSET,
    page_number: Union[Unset, int] = 1,
    page_size: Union[Unset, int] = 10,
) -> Response[PaginatedListOfRecordDto]:
    """
    Args:
        mini_id (Union[None, Unset, str]):
        session_id (Union[None, Unset, str]):
        page_number (Union[Unset, int]):  Default: 1.
        page_size (Union[Unset, int]):  Default: 10.
        body (list[str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PaginatedListOfRecordDto]
    """

    kwargs = _get_kwargs(
        body=body,
        mini_id=mini_id,
        session_id=session_id,
        page_number=page_number,
        page_size=page_size,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    body: list[str],
    mini_id: Union[None, Unset, str] = UNSET,
    session_id: Union[None, Unset, str] = UNSET,
    page_number: Union[Unset, int] = 1,
    page_size: Union[Unset, int] = 10,
) -> Optional[PaginatedListOfRecordDto]:
    """
    Args:
        mini_id (Union[None, Unset, str]):
        session_id (Union[None, Unset, str]):
        page_number (Union[Unset, int]):  Default: 1.
        page_size (Union[Unset, int]):  Default: 10.
        body (list[str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PaginatedListOfRecordDto
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            mini_id=mini_id,
            session_id=session_id,
            page_number=page_number,
            page_size=page_size,
        )
    ).parsed
