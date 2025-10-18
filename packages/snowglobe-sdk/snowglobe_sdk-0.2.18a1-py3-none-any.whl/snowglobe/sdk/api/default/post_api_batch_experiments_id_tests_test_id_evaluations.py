from http import HTTPStatus
from typing import Any, Optional, Union, cast

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.http_error import HttpError
from ...models.risk_evaluation_batch_create_request_item import (
    RiskEvaluationBatchCreateRequestItem,
)
from ...models.risk_evaluations_item import RiskEvaluationsItem
from ...models.validation_error import ValidationError
from ...types import Unset


def _get_kwargs(
    id: str,
    test_id: str,
    *,
    body: list["RiskEvaluationBatchCreateRequestItem"],
    tests: Union[Unset, str] = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    params: dict[str, Any] = {}

    params["tests"] = tests

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/batch/experiments/{id}/tests/{test_id}/evaluations".format(
            id=id,
            test_id=test_id,
        ),
        "params": params,
    }

    _kwargs["json"] = []
    for componentsschemas_risk_evaluation_batch_create_request_item_data in body:
        componentsschemas_risk_evaluation_batch_create_request_item = (
            componentsschemas_risk_evaluation_batch_create_request_item_data.to_dict()
        )
        _kwargs["json"].append(
            componentsschemas_risk_evaluation_batch_create_request_item
        )

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[Any, HttpError, ValidationError, list["RiskEvaluationsItem"]]]:
    if response.status_code == 201:
        response_201 = []
        _response_201 = response.json()
        for componentsschemas_risk_evaluations_item_data in _response_201:
            componentsschemas_risk_evaluations_item = RiskEvaluationsItem.from_dict(
                componentsschemas_risk_evaluations_item_data
            )

            response_201.append(componentsschemas_risk_evaluations_item)

        return response_201

    if response.status_code == 204:
        response_204 = cast(Any, None)
        return response_204

    if response.status_code == 400:
        response_400 = HttpError.from_dict(response.json())

        return response_400

    if response.status_code == 403:
        response_403 = HttpError.from_dict(response.json())

        return response_403

    if response.status_code == 404:
        response_404 = HttpError.from_dict(response.json())

        return response_404

    if response.status_code == 422:
        response_422 = ValidationError.from_dict(response.json())

        return response_422

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[Any, HttpError, ValidationError, list["RiskEvaluationsItem"]]]:
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
    body: list["RiskEvaluationBatchCreateRequestItem"],
    tests: Union[Unset, str] = UNSET,
) -> Response[Union[Any, HttpError, ValidationError, list["RiskEvaluationsItem"]]]:
    """Create multiple risk evaluations for a test

    Args:
        id (str):
        test_id (str):
        tests (Union[Unset, str]):
        body (list['RiskEvaluationBatchCreateRequestItem']):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, HttpError, ValidationError, list['RiskEvaluationsItem']]]
    """

    kwargs = _get_kwargs(
        id=id,
        test_id=test_id,
        body=body,
        tests=tests,
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
    body: list["RiskEvaluationBatchCreateRequestItem"],
    tests: Union[Unset, str] = UNSET,
) -> Optional[Union[Any, HttpError, ValidationError, list["RiskEvaluationsItem"]]]:
    """Create multiple risk evaluations for a test

    Args:
        id (str):
        test_id (str):
        tests (Union[Unset, str]):
        body (list['RiskEvaluationBatchCreateRequestItem']):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, HttpError, ValidationError, list['RiskEvaluationsItem']]
    """

    return sync_detailed(
        id=id,
        test_id=test_id,
        client=client,
        body=body,
        tests=tests,
    ).parsed


async def asyncio_detailed(
    id: str,
    test_id: str,
    *,
    client: Union[AuthenticatedClient, Client],
    body: list["RiskEvaluationBatchCreateRequestItem"],
    tests: Union[Unset, str] = UNSET,
) -> Response[Union[Any, HttpError, ValidationError, list["RiskEvaluationsItem"]]]:
    """Create multiple risk evaluations for a test

    Args:
        id (str):
        test_id (str):
        tests (Union[Unset, str]):
        body (list['RiskEvaluationBatchCreateRequestItem']):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, HttpError, ValidationError, list['RiskEvaluationsItem']]]
    """

    kwargs = _get_kwargs(
        id=id,
        test_id=test_id,
        body=body,
        tests=tests,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    id: str,
    test_id: str,
    *,
    client: Union[AuthenticatedClient, Client],
    body: list["RiskEvaluationBatchCreateRequestItem"],
    tests: Union[Unset, str] = UNSET,
) -> Optional[Union[Any, HttpError, ValidationError, list["RiskEvaluationsItem"]]]:
    """Create multiple risk evaluations for a test

    Args:
        id (str):
        test_id (str):
        tests (Union[Unset, str]):
        body (list['RiskEvaluationBatchCreateRequestItem']):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, HttpError, ValidationError, list['RiskEvaluationsItem']]
    """

    return (
        await asyncio_detailed(
            id=id,
            test_id=test_id,
            client=client,
            body=body,
            tests=tests,
        )
    ).parsed
