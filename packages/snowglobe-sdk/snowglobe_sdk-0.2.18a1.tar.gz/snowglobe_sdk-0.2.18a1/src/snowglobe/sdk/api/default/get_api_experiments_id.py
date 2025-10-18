from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.experiment import Experiment
from ...models.http_error import HttpError
from ...types import Unset


def _get_kwargs(
    id: str,
    *,
    exclude_calculated_status: Union[Unset, bool] = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["exclude-calculated-status"] = exclude_calculated_status

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/experiments/{id}".format(
            id=id,
        ),
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[Experiment, HttpError]]:
    if response.status_code == 200:
        response_200 = Experiment.from_dict(response.json())

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
) -> Response[Union[Experiment, HttpError]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    id: str,
    *,
    client: Union[AuthenticatedClient, Client],
    exclude_calculated_status: Union[Unset, bool] = UNSET,
) -> Response[Union[Experiment, HttpError]]:
    """Get an experiment by ID

    Args:
        id (str):
        exclude_calculated_status (Union[Unset, bool]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Experiment, HttpError]]
    """

    kwargs = _get_kwargs(
        id=id,
        exclude_calculated_status=exclude_calculated_status,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    id: str,
    *,
    client: Union[AuthenticatedClient, Client],
    exclude_calculated_status: Union[Unset, bool] = UNSET,
) -> Optional[Union[Experiment, HttpError]]:
    """Get an experiment by ID

    Args:
        id (str):
        exclude_calculated_status (Union[Unset, bool]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Experiment, HttpError]
    """

    return sync_detailed(
        id=id,
        client=client,
        exclude_calculated_status=exclude_calculated_status,
    ).parsed


async def asyncio_detailed(
    id: str,
    *,
    client: Union[AuthenticatedClient, Client],
    exclude_calculated_status: Union[Unset, bool] = UNSET,
) -> Response[Union[Experiment, HttpError]]:
    """Get an experiment by ID

    Args:
        id (str):
        exclude_calculated_status (Union[Unset, bool]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Experiment, HttpError]]
    """

    kwargs = _get_kwargs(
        id=id,
        exclude_calculated_status=exclude_calculated_status,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    id: str,
    *,
    client: Union[AuthenticatedClient, Client],
    exclude_calculated_status: Union[Unset, bool] = UNSET,
) -> Optional[Union[Experiment, HttpError]]:
    """Get an experiment by ID

    Args:
        id (str):
        exclude_calculated_status (Union[Unset, bool]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Experiment, HttpError]
    """

    return (
        await asyncio_detailed(
            id=id,
            client=client,
            exclude_calculated_status=exclude_calculated_status,
        )
    ).parsed
