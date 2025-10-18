from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.conversations_item import ConversationsItem
from ...models.http_error import HttpError
from ...types import Unset


def _get_kwargs(
    id: str,
    test_id: str,
    *,
    start_from: Union[Unset, str] = UNSET,
    app_id: Union[Unset, str] = UNSET,
    include_adaptability_messages: Union[Unset, bool] = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["start-from"] = start_from

    params["appId"] = app_id

    params["include-adaptability-messages"] = include_adaptability_messages

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/experiments/{id}/tests/{test_id}/conversations".format(
            id=id,
            test_id=test_id,
        ),
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[HttpError, list["ConversationsItem"]]]:
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.json()
        for componentsschemas_conversations_item_data in _response_200:
            componentsschemas_conversations_item = ConversationsItem.from_dict(
                componentsschemas_conversations_item_data
            )

            response_200.append(componentsschemas_conversations_item)

        return response_200

    if response.status_code == 400:
        response_400 = HttpError.from_dict(response.json())

        return response_400

    if response.status_code == 403:
        response_403 = HttpError.from_dict(response.json())

        return response_403

    if response.status_code == 404:
        response_404 = HttpError.from_dict(response.json())

        return response_404

    if response.status_code == 500:
        response_500 = HttpError.from_dict(response.json())

        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[HttpError, list["ConversationsItem"]]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    id: str,
    test_id: str,
    *,
    client: Union[AuthenticatedClient, Client],
    start_from: Union[Unset, str] = UNSET,
    app_id: Union[Unset, str] = UNSET,
    include_adaptability_messages: Union[Unset, bool] = UNSET,
) -> Response[Union[HttpError, list["ConversationsItem"]]]:
    """Get Conversations for a Test

    Args:
        id (str):
        test_id (str):
        start_from (Union[Unset, str]):
        app_id (Union[Unset, str]):
        include_adaptability_messages (Union[Unset, bool]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HttpError, list['ConversationsItem']]]
    """

    kwargs = _get_kwargs(
        id=id,
        test_id=test_id,
        start_from=start_from,
        app_id=app_id,
        include_adaptability_messages=include_adaptability_messages,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    id: str,
    test_id: str,
    *,
    client: Union[AuthenticatedClient, Client],
    start_from: Union[Unset, str] = UNSET,
    app_id: Union[Unset, str] = UNSET,
    include_adaptability_messages: Union[Unset, bool] = UNSET,
) -> Optional[Union[HttpError, list["ConversationsItem"]]]:
    """Get Conversations for a Test

    Args:
        id (str):
        test_id (str):
        start_from (Union[Unset, str]):
        app_id (Union[Unset, str]):
        include_adaptability_messages (Union[Unset, bool]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HttpError, list['ConversationsItem']]
    """

    return sync_detailed(
        id=id,
        test_id=test_id,
        client=client,
        start_from=start_from,
        app_id=app_id,
        include_adaptability_messages=include_adaptability_messages,
    ).parsed


async def asyncio_detailed(
    id: str,
    test_id: str,
    *,
    client: Union[AuthenticatedClient, Client],
    start_from: Union[Unset, str] = UNSET,
    app_id: Union[Unset, str] = UNSET,
    include_adaptability_messages: Union[Unset, bool] = UNSET,
) -> Response[Union[HttpError, list["ConversationsItem"]]]:
    """Get Conversations for a Test

    Args:
        id (str):
        test_id (str):
        start_from (Union[Unset, str]):
        app_id (Union[Unset, str]):
        include_adaptability_messages (Union[Unset, bool]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HttpError, list['ConversationsItem']]]
    """

    kwargs = _get_kwargs(
        id=id,
        test_id=test_id,
        start_from=start_from,
        app_id=app_id,
        include_adaptability_messages=include_adaptability_messages,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    id: str,
    test_id: str,
    *,
    client: Union[AuthenticatedClient, Client],
    start_from: Union[Unset, str] = UNSET,
    app_id: Union[Unset, str] = UNSET,
    include_adaptability_messages: Union[Unset, bool] = UNSET,
) -> Optional[Union[HttpError, list["ConversationsItem"]]]:
    """Get Conversations for a Test

    Args:
        id (str):
        test_id (str):
        start_from (Union[Unset, str]):
        app_id (Union[Unset, str]):
        include_adaptability_messages (Union[Unset, bool]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HttpError, list['ConversationsItem']]
    """

    return (
        await asyncio_detailed(
            id=id,
            test_id=test_id,
            client=client,
            start_from=start_from,
            app_id=app_id,
            include_adaptability_messages=include_adaptability_messages,
        )
    ).parsed
