from http import HTTPStatus
from typing import Any, Optional, Union, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.geoteknisk_unders import GeotekniskUnders
from ...types import Response


def _get_kwargs(
    code_list_name: str,
    code_name: str,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/nadag/innmelding/v1/kodeliste/{code_list_name}/{code_name}",
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[Any, GeotekniskUnders]]:
    if response.status_code == 200:
        response_200 = GeotekniskUnders.from_dict(response.json())

        return response_200

    if response.status_code == 404:
        response_404 = cast(Any, None)
        return response_404

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[Any, GeotekniskUnders]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    code_list_name: str,
    code_name: str,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Response[Union[Any, GeotekniskUnders]]:
    """Retrieves a code in a code list.

     Fetches a code in a code list.

    Args:
        code_list_name (str):
        code_name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, GeotekniskUnders]]
    """

    kwargs = _get_kwargs(
        code_list_name=code_list_name,
        code_name=code_name,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    code_list_name: str,
    code_name: str,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Optional[Union[Any, GeotekniskUnders]]:
    """Retrieves a code in a code list.

     Fetches a code in a code list.

    Args:
        code_list_name (str):
        code_name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, GeotekniskUnders]
    """

    return sync_detailed(
        code_list_name=code_list_name,
        code_name=code_name,
        client=client,
    ).parsed


async def asyncio_detailed(
    code_list_name: str,
    code_name: str,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Response[Union[Any, GeotekniskUnders]]:
    """Retrieves a code in a code list.

     Fetches a code in a code list.

    Args:
        code_list_name (str):
        code_name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, GeotekniskUnders]]
    """

    kwargs = _get_kwargs(
        code_list_name=code_list_name,
        code_name=code_name,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    code_list_name: str,
    code_name: str,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Optional[Union[Any, GeotekniskUnders]]:
    """Retrieves a code in a code list.

     Fetches a code in a code list.

    Args:
        code_list_name (str):
        code_name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, GeotekniskUnders]
    """

    return (
        await asyncio_detailed(
            code_list_name=code_list_name,
            code_name=code_name,
            client=client,
        )
    ).parsed
