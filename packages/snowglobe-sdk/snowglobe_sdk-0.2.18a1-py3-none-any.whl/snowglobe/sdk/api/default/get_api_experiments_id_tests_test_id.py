from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.http_error import HttpError
from ...models.test_with_risk_evaluations import TestWithRiskEvaluations
from ...types import Unset


def _get_kwargs(
    id: str,
    test_id: str,
    *,
    include_embedding: Union[Unset, bool] = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["include-embedding"] = include_embedding

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/experiments/{id}/tests/{test_id}".format(
            id=id,
            test_id=test_id,
        ),
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[HttpError, TestWithRiskEvaluations]]:
    if response.status_code == 200:
        response_200 = TestWithRiskEvaluations.from_dict(response.json())

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

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[HttpError, TestWithRiskEvaluations]]:
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
    include_embedding: Union[Unset, bool] = UNSET,
) -> Response[Union[HttpError, TestWithRiskEvaluations]]:
    """Get a test by ID

    Args:
        id (str):
        test_id (str):
        include_embedding (Union[Unset, bool]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HttpError, TestWithRiskEvaluations]]
    """

    kwargs = _get_kwargs(
        id=id,
        test_id=test_id,
        include_embedding=include_embedding,
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
    include_embedding: Union[Unset, bool] = UNSET,
) -> Optional[Union[HttpError, TestWithRiskEvaluations]]:
    """Get a test by ID

    Args:
        id (str):
        test_id (str):
        include_embedding (Union[Unset, bool]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HttpError, TestWithRiskEvaluations]
    """

    return sync_detailed(
        id=id,
        test_id=test_id,
        client=client,
        include_embedding=include_embedding,
    ).parsed


async def asyncio_detailed(
    id: str,
    test_id: str,
    *,
    client: Union[AuthenticatedClient, Client],
    include_embedding: Union[Unset, bool] = UNSET,
) -> Response[Union[HttpError, TestWithRiskEvaluations]]:
    """Get a test by ID

    Args:
        id (str):
        test_id (str):
        include_embedding (Union[Unset, bool]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HttpError, TestWithRiskEvaluations]]
    """

    kwargs = _get_kwargs(
        id=id,
        test_id=test_id,
        include_embedding=include_embedding,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    id: str,
    test_id: str,
    *,
    client: Union[AuthenticatedClient, Client],
    include_embedding: Union[Unset, bool] = UNSET,
) -> Optional[Union[HttpError, TestWithRiskEvaluations]]:
    """Get a test by ID

    Args:
        id (str):
        test_id (str):
        include_embedding (Union[Unset, bool]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HttpError, TestWithRiskEvaluations]
    """

    return (
        await asyncio_detailed(
            id=id,
            test_id=test_id,
            client=client,
            include_embedding=include_embedding,
        )
    ).parsed
