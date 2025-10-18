from http import HTTPStatus
from typing import Any, Optional, Union, cast

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.simulation import Simulation
from ...models.simulation_create_schema import SimulationCreateSchema
from ...models.validation_error import ValidationError
from ...types import Unset


def _get_kwargs(
    *,
    body: SimulationCreateSchema,
    as_draft: Union[Unset, str] = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    params: dict[str, Any] = {}

    params["asDraft"] = as_draft

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/simulations",
        "params": params,
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[Any, Simulation, ValidationError]]:
    if response.status_code == 201:
        response_201 = Simulation.from_dict(response.json())

        return response_201

    if response.status_code == 400:
        response_400 = cast(Any, None)
        return response_400

    if response.status_code == 422:
        response_422 = ValidationError.from_dict(response.json())

        return response_422

    if response.status_code == 500:
        response_500 = cast(Any, None)
        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[Any, Simulation, ValidationError]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: SimulationCreateSchema,
    as_draft: Union[Unset, str] = UNSET,
) -> Response[Union[Any, Simulation, ValidationError]]:
    """Create a new simulation

    Args:
        as_draft (Union[Unset, str]):
        body (SimulationCreateSchema):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, Simulation, ValidationError]]
    """

    kwargs = _get_kwargs(
        body=body,
        as_draft=as_draft,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    body: SimulationCreateSchema,
    as_draft: Union[Unset, str] = UNSET,
) -> Optional[Union[Any, Simulation, ValidationError]]:
    """Create a new simulation

    Args:
        as_draft (Union[Unset, str]):
        body (SimulationCreateSchema):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, Simulation, ValidationError]
    """

    return sync_detailed(
        client=client,
        body=body,
        as_draft=as_draft,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: SimulationCreateSchema,
    as_draft: Union[Unset, str] = UNSET,
) -> Response[Union[Any, Simulation, ValidationError]]:
    """Create a new simulation

    Args:
        as_draft (Union[Unset, str]):
        body (SimulationCreateSchema):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, Simulation, ValidationError]]
    """

    kwargs = _get_kwargs(
        body=body,
        as_draft=as_draft,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    body: SimulationCreateSchema,
    as_draft: Union[Unset, str] = UNSET,
) -> Optional[Union[Any, Simulation, ValidationError]]:
    """Create a new simulation

    Args:
        as_draft (Union[Unset, str]):
        body (SimulationCreateSchema):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, Simulation, ValidationError]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            as_draft=as_draft,
        )
    ).parsed
