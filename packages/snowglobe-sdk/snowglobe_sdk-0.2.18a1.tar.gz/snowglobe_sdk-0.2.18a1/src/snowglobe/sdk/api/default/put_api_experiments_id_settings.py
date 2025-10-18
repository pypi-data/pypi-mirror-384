from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.experiment_settings_update_schema import ExperimentSettingsUpdateSchema
from ...models.http_error import HttpError
from ...types import Unset


def _get_kwargs(
    id: str,
    *,
    body: ExperimentSettingsUpdateSchema,
    access: Union[Unset, str] = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    params: dict[str, Any] = {}

    params["access"] = access

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "put",
        "url": "/api/experiments/{id}/settings".format(
            id=id,
        ),
        "params": params,
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[ExperimentSettingsUpdateSchema, HttpError]]:
    if response.status_code == 200:
        response_200 = ExperimentSettingsUpdateSchema.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = HttpError.from_dict(response.json())

        return response_400

    if response.status_code == 403:
        response_403 = HttpError.from_dict(response.json())

        return response_403

    if response.status_code == 500:
        response_500 = HttpError.from_dict(response.json())

        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[ExperimentSettingsUpdateSchema, HttpError]]:
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
    body: ExperimentSettingsUpdateSchema,
    access: Union[Unset, str] = UNSET,
) -> Response[Union[ExperimentSettingsUpdateSchema, HttpError]]:
    """Update settings for an experiment

    Args:
        id (str):
        access (Union[Unset, str]):
        body (ExperimentSettingsUpdateSchema):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ExperimentSettingsUpdateSchema, HttpError]]
    """

    kwargs = _get_kwargs(
        id=id,
        body=body,
        access=access,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    id: str,
    *,
    client: Union[AuthenticatedClient, Client],
    body: ExperimentSettingsUpdateSchema,
    access: Union[Unset, str] = UNSET,
) -> Optional[Union[ExperimentSettingsUpdateSchema, HttpError]]:
    """Update settings for an experiment

    Args:
        id (str):
        access (Union[Unset, str]):
        body (ExperimentSettingsUpdateSchema):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ExperimentSettingsUpdateSchema, HttpError]
    """

    return sync_detailed(
        id=id,
        client=client,
        body=body,
        access=access,
    ).parsed


async def asyncio_detailed(
    id: str,
    *,
    client: Union[AuthenticatedClient, Client],
    body: ExperimentSettingsUpdateSchema,
    access: Union[Unset, str] = UNSET,
) -> Response[Union[ExperimentSettingsUpdateSchema, HttpError]]:
    """Update settings for an experiment

    Args:
        id (str):
        access (Union[Unset, str]):
        body (ExperimentSettingsUpdateSchema):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ExperimentSettingsUpdateSchema, HttpError]]
    """

    kwargs = _get_kwargs(
        id=id,
        body=body,
        access=access,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    id: str,
    *,
    client: Union[AuthenticatedClient, Client],
    body: ExperimentSettingsUpdateSchema,
    access: Union[Unset, str] = UNSET,
) -> Optional[Union[ExperimentSettingsUpdateSchema, HttpError]]:
    """Update settings for an experiment

    Args:
        id (str):
        access (Union[Unset, str]):
        body (ExperimentSettingsUpdateSchema):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ExperimentSettingsUpdateSchema, HttpError]
    """

    return (
        await asyncio_detailed(
            id=id,
            client=client,
            body=body,
            access=access,
        )
    ).parsed
