from http import HTTPStatus
from typing import Any, Dict, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.setup_ducklake_catalog_db_response_200 import SetupDucklakeCatalogDbResponse200
from ...types import Response


def _get_kwargs(
    name: str,
) -> Dict[str, Any]:
    pass

    return {
        "method": "post",
        "url": "/settings/setup_ducklake_catalog_db/{name}".format(
            name=name,
        ),
    }


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[SetupDucklakeCatalogDbResponse200]:
    if response.status_code == HTTPStatus.OK:
        response_200 = SetupDucklakeCatalogDbResponse200.from_dict(response.json())

        return response_200
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[SetupDucklakeCatalogDbResponse200]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    name: str,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Response[SetupDucklakeCatalogDbResponse200]:
    """Runs CREATE DATABASE on the Windmill Postgres and grants access to the ducklake_user

    Args:
        name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[SetupDucklakeCatalogDbResponse200]
    """

    kwargs = _get_kwargs(
        name=name,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    name: str,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Optional[SetupDucklakeCatalogDbResponse200]:
    """Runs CREATE DATABASE on the Windmill Postgres and grants access to the ducklake_user

    Args:
        name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        SetupDucklakeCatalogDbResponse200
    """

    return sync_detailed(
        name=name,
        client=client,
    ).parsed


async def asyncio_detailed(
    name: str,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Response[SetupDucklakeCatalogDbResponse200]:
    """Runs CREATE DATABASE on the Windmill Postgres and grants access to the ducklake_user

    Args:
        name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[SetupDucklakeCatalogDbResponse200]
    """

    kwargs = _get_kwargs(
        name=name,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    name: str,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Optional[SetupDucklakeCatalogDbResponse200]:
    """Runs CREATE DATABASE on the Windmill Postgres and grants access to the ducklake_user

    Args:
        name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        SetupDucklakeCatalogDbResponse200
    """

    return (
        await asyncio_detailed(
            name=name,
            client=client,
        )
    ).parsed
